import { HomeTaskerBase } from "./main.js";
import { esc } from "./shared.js";

export const UNASSIGNED = "__unassigned__";
export const DEFAULT_CARD_CONFIG = Object.freeze({
  type: "custom:home-tasker-card",
  mode: "view",
  due_days: 0,
  group_ids: [],
  assignee_user_ids: [],
  sort_direction: "asc",
});

export function normalizeCardConfig(config={}) {
  const dueDays=config.due_days===null?null:Number.isInteger(Number(config.due_days))&&Number(config.due_days)>=0?Number(config.due_days):0;
  return {
    ...DEFAULT_CARD_CONFIG,
    ...config,
    mode:config.mode==="edit"?"edit":"view",
    due_days:dueDays,
    group_ids:Array.isArray(config.group_ids)?[...config.group_ids]:[],
    assignee_user_ids:Array.isArray(config.assignee_user_ids)?[...config.assignee_user_ids]:[],
    sort_direction:config.sort_direction==="desc"?"desc":"asc",
  };
}

function addDays(iso,days){const match=/^(\d{4})-(\d{2})-(\d{2})$/.exec(iso||"");if(!match)return null;const value=new Date(Date.UTC(+match[1],+match[2]-1,+match[3]+days));return value.toISOString().slice(0,10);}

export function filterDashboardTasks(tasks,config,today){
  const cfg=normalizeCardConfig(config),limit=cfg.due_days===null?null:addDays(today,cfg.due_days);
  return tasks.filter(task=>{
    if(limit&&(!task.due_date||task.due_date>limit))return false;
    if(cfg.group_ids.length&&!cfg.group_ids.includes(task.group_id))return false;
    if(cfg.assignee_user_ids.length){const assignee=task.assignee_user_id||UNASSIGNED;if(!cfg.assignee_user_ids.includes(assignee))return false;}
    return true;
  });
}

export function sortDashboardTasks(tasks,direction="asc",locale="de"){
  const factor=direction==="desc"?-1:1;
  return [...tasks].sort((a,b)=>factor*(a.due_date||"").localeCompare(b.due_date||"")||(a.name||"").localeCompare(b.name||"",locale));
}

export function dashboardTaskRowHtml(task,editable,relativeDate){return `<div class="task-row${editable?" editable":""}" data-task="${esc(task.id)}" tabindex="0"><div><div class="task-name">${esc(task.name)}</div><div class="due-label">${esc(relativeDate)}</div></div>${editable?'<button type="button" class="edit-task-row icon" aria-label="Task bearbeiten" title="Task bearbeiten"><ha-icon icon="mdi:pencil"></ha-icon></button>':""}</div>`;}
export function canEditCard(config,hass){return normalizeCardConfig(config).mode==="edit"&&Boolean(hass?.user?.is_admin);}

export class HomeTaskerCard extends HomeTaskerBase {
  static getStubConfig(){return {...DEFAULT_CARD_CONFIG};}
  static async getConfigElement(){return document.createElement("home-tasker-card-editor");}
  setConfig(config){this.config=normalizeCardConfig(config);if(this.loaded)this.render();}
  getCardSize(){return Math.max(1,Math.min(8,this.visibleTasks().length+1));}
  visibleTasks(){return sortDashboardTasks(filterDashboardTasks(this.tasks||[],this.config||DEFAULT_CARD_CONFIG,this.today),(this.config||DEFAULT_CARD_CONFIG).sort_direction,this.locale());}
  render(){
    if(!this.shadowRoot.querySelector(".card-root"))this.shadowRoot.innerHTML=`${this.styles()}<style>:host{display:block}ha-card{overflow:hidden}.card-content{padding:0}.task-row{display:grid;grid-template-columns:minmax(0,1fr);align-items:center;min-height:52px;padding:4px 12px;border-top:1px solid var(--divider-color);cursor:pointer}.task-row:first-child{border-top:0}.task-row:hover{background:rgba(var(--rgb-primary-text-color),.04)}.task-row.editable{grid-template-columns:minmax(0,1fr) 44px}.task-name{color:var(--primary-text-color);font-weight:var(--ha-font-weight-normal,400)}.due-label{color:var(--secondary-text-color);font-size:var(--ha-font-size-s,12px)}.empty{padding:20px;color:var(--secondary-text-color);text-align:center}.card-actions{display:flex;justify-content:flex-end;padding:8px 12px;border-top:1px solid var(--divider-color)}.add-task{display:flex;align-items:center;gap:7px;background:var(--primary-color);color:var(--text-primary-color,#fff)}</style><div class="card-root"></div><div class="dialogs"></div>`;
    const root=this.shadowRoot.querySelector(".card-root"),tasks=this.visibleTasks(),editable=canEditCard(this.config,this._hass);
    root.innerHTML=`<ha-card><div class="card-content">${tasks.length?tasks.map(task=>dashboardTaskRowHtml(task,editable,this.relativeDate(task.due_date))).join(""):'<div class="empty">Keine passenden Tasks</div>'}</div>${editable?'<div class="card-actions"><button type="button" class="add-task"><ha-icon icon="mdi:plus"></ha-icon><span>Task hinzufügen</span></button></div>':""}</ha-card>`;
    root.insertAdjacentHTML("beforeend",this.themeStyles()+this.buttonThemeStyles()+this.compactDetailsStyles()+this.iconHoverStyles());
    root.querySelectorAll("[data-task]").forEach(row=>{const task=this.tasks.find(item=>item.id===row.dataset.task);row.onclick=()=>this.taskViewer(task);row.onkeydown=event=>{if(event.target===row&&(event.key==="Enter"||event.key===" "))this.taskViewer(task);};const edit=row.querySelector(".edit-task-row");if(edit)edit.onclick=event=>{event.stopPropagation();this.taskEditor(task.group_id,task);};});
    const add=root.querySelector(".add-task");if(add)add.onclick=()=>this.taskEditor(null);
  }
}

export class HomeTaskerCardEditor extends HTMLElement {
  constructor(){super();this.attachShadow({mode:"open"});this.config={...DEFAULT_CARD_CONFIG};this.groups=[];this.users=[];this.loaded=false;}
  set hass(value){this._hass=value;if(!this.loaded){this.loaded=true;this.load();}else this.render();}
  setConfig(config){this.config=normalizeCardConfig(config);this.render();}
  async load(){try{const data=await this._hass.connection.sendMessagePromise({type:"home_tasker/list"});this.groups=data.groups||[];this.users=data.users||[];}catch(error){console.error("Home Tasker card editor load failed",error);}this.render();}
  update(patch){this.config=normalizeCardConfig({...this.config,...patch});this.dispatchEvent(new CustomEvent("config-changed",{detail:{config:{...this.config}},bubbles:true,composed:true}));this.render();}
  checks(items,selected,name){return items.map(item=>`<label><input type="checkbox" name="${name}" value="${esc(item.id)}" ${selected.includes(item.id)?"checked":""}><span>${esc(item.name)}</span></label>`).join("");}
  render(){if(!this.shadowRoot)return;this.shadowRoot.innerHTML=`<style>:host{display:block}.editor{display:grid;gap:16px}.field{display:grid;gap:7px}.choices{display:grid;gap:6px;max-height:180px;overflow:auto;padding:8px;border:1px solid var(--divider-color);border-radius:8px}.choices label{display:flex;gap:8px;align-items:center}select,input[type=number]{box-sizing:border-box;width:100%;padding:9px;border:1px solid var(--divider-color);border-radius:8px;background:var(--card-background-color);color:var(--primary-text-color)}</style><div class="editor"><label class="field"><span>Modus</span><select name="mode"><option value="view" ${this.config.mode==="view"?"selected":""}>Anzeigen</option><option value="edit" ${this.config.mode==="edit"?"selected":""}>Bearbeiten</option></select></label><label class="field"><span>Tage in die Zukunft (leer = alle)</span><input name="due_days" type="number" min="0" step="1" value="${this.config.due_days??""}"></label><div class="field"><span>Gruppen (keine Auswahl = alle)</span><div class="choices groups">${this.checks(this.groups,this.config.group_ids,"groups")||"Keine Gruppen vorhanden"}</div></div><div class="field"><span>Benutzer (keine Auswahl = alle)</span><div class="choices users">${this.checks([{id:UNASSIGNED,name:"Nicht zugewiesen"},...this.users],this.config.assignee_user_ids,"users")}</div></div><label class="field"><span>Sortierrichtung</span><select name="sort_direction"><option value="asc" ${this.config.sort_direction==="asc"?"selected":""}>Älteste zuerst</option><option value="desc" ${this.config.sort_direction==="desc"?"selected":""}>Neueste zuerst</option></select></label></div>`;
    this.shadowRoot.querySelector('[name="mode"]').onchange=event=>this.update({mode:event.target.value});this.shadowRoot.querySelector('[name="sort_direction"]').onchange=event=>this.update({sort_direction:event.target.value});this.shadowRoot.querySelector('[name="due_days"]').onchange=event=>this.update({due_days:event.target.value===""?null:Math.max(0,Math.trunc(Number(event.target.value)||0))});for(const [selector,key] of [[".groups","group_ids"],[".users","assignee_user_ids"]])this.shadowRoot.querySelector(selector).onchange=()=>this.update({[key]:[...this.shadowRoot.querySelectorAll(`${selector} input:checked`)].map(input=>input.value)});
  }
}

if(!customElements.get("home-tasker-card"))customElements.define("home-tasker-card",HomeTaskerCard);
if(!customElements.get("home-tasker-card-editor"))customElements.define("home-tasker-card-editor",HomeTaskerCardEditor);
window.customCards=window.customCards||[];
if(!window.customCards.some(card=>card.type==="home-tasker-card"))window.customCards.push({type:"home-tasker-card",name:"Home Tasker",description:"Fällige Home-Tasker-Aufgaben als flache Liste"});
