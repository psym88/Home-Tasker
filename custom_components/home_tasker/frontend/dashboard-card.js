import { HomeTaskerBase } from "./main.js";
import { esc } from "./shared.js";
import { ROW_ACTION_MENU_STYLES, rowActionButtonHtml } from "./action-menu.js";

export const UNASSIGNED = "__unassigned__";
export const DEFAULT_CARD_CONFIG = Object.freeze({
  type: "custom:home-tasker-card",
  mode: "view",
  due_days: 0,
  group_ids: [],
  assignee_user_ids: [],
  hide_card_background: false,
});

export function normalizeCardConfig(config={}) {
  const supportedConfig={...config};
  delete supportedConfig.sort_direction;
  const dueDays=config.due_days===null?null:Number.isInteger(Number(config.due_days))&&Number(config.due_days)>=0?Number(config.due_days):0;
  return {
    ...DEFAULT_CARD_CONFIG,
    ...supportedConfig,
    mode:config.mode==="edit"?"edit":"view",
    due_days:dueDays,
    group_ids:Array.isArray(config.group_ids)?[...config.group_ids]:[],
    assignee_user_ids:Array.isArray(config.assignee_user_ids)?[...config.assignee_user_ids]:[],
    hide_card_background:config.hide_card_background===true,
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

export function sortDashboardTasks(tasks,locale="de"){
  return [...tasks].sort((a,b)=>(a.due_date||"").localeCompare(b.due_date||"")||(a.name||"").localeCompare(b.name||"",locale));
}

export function dueStatus(dueDate,today){return dueDate<today?"overdue":dueDate===today?"today":"future";}
export function dashboardTaskRowHtml(task,editable,relativeDate,status){return `<div class="task-row${editable?" editable":""}" data-task="${esc(task.id)}" tabindex="0"><div><div class="task-name">${esc(task.name)}</div><div class="due-label ${esc(status)}">${esc(relativeDate)}</div></div>${editable?rowActionButtonHtml("task",esc(task.id)):""}</div>`;}
export function dashboardCardBodyHtml(rows,editable,hideCardBackground=false){return `<ha-card${hideCardBackground?' class="no-card-background" style="border:0;background:transparent;box-shadow:none"':""}>${editable?'<div class="card-actions"><button type="button" class="add-task"><ha-icon icon="mdi:plus"></ha-icon><span>Task hinzufügen</span></button></div>':""}<div class="card-content">${rows||'<div class="empty">Keine passenden Tasks</div>'}</div></ha-card>`;}
export function canEditCard(config,hass){return normalizeCardConfig(config).mode==="edit"&&Boolean(hass?.user?.is_admin);}

export class HomeTaskerCard extends HomeTaskerBase {
  static getStubConfig(){return {...DEFAULT_CARD_CONFIG};}
  static async getConfigElement(){return document.createElement("home-tasker-card-editor");}
  setConfig(config){this.config=normalizeCardConfig(config);if(this.loaded)this.render();}
  getCardSize(){return Math.max(1,Math.min(8,this.visibleTasks().length+1));}
  visibleTasks(){return sortDashboardTasks(filterDashboardTasks(this.tasks||[],this.config||DEFAULT_CARD_CONFIG,this.today),this.locale());}
  render(){
    this.closeActionMenu();
    if(!this.shadowRoot.querySelector(".card-root"))this.shadowRoot.innerHTML=`${this.styles()}<style>:host{display:block}ha-card{overflow:hidden}.card-content{display:grid;gap:8px;padding:12px}.task-row{display:grid;grid-template-columns:minmax(0,1fr);align-items:center;min-height:52px;padding:4px 12px;border:1px solid var(--divider-color);border-radius:10px;background:var(--secondary-background-color);cursor:pointer}.task-row:hover{background:rgba(var(--rgb-primary-text-color),.04)}.task-row.editable{grid-template-columns:minmax(0,1fr) 44px}.task-name{color:var(--primary-text-color);font-weight:var(--ha-font-weight-normal,400)}.due-label{display:inline-flex;margin-top:3px;font-size:var(--ha-font-size-s,12px);font-weight:var(--ha-font-weight-medium,500)}.due-label.today{color:var(--warning-color,#f57c00)}.due-label.overdue{color:var(--error-color,#d32f2f)}.due-label.future{color:var(--success-color,#43a047)}.empty{padding:20px;color:var(--secondary-text-color);text-align:center}.card-actions{display:flex;justify-content:flex-end;padding:12px 12px 0}.add-task{display:flex;align-items:center;gap:7px;background:var(--primary-color);color:var(--text-primary-color,#fff)}</style><div class="card-root"></div>`;
    const root=this.shadowRoot.querySelector(".card-root"),tasks=this.visibleTasks(),editable=canEditCard(this.config,this._hass);
    root.innerHTML=dashboardCardBodyHtml(tasks.map(task=>dashboardTaskRowHtml(task,editable,this.relativeDate(task.due_date),dueStatus(task.due_date,this.today))).join(""),editable,this.config.hide_card_background);
    root.insertAdjacentHTML("beforeend",ROW_ACTION_MENU_STYLES+this.themeStyles()+this.iconHoverStyles());
    root.querySelectorAll("[data-task]").forEach(row=>{const task=this.tasks.find(item=>item.id===row.dataset.task);row.onclick=()=>this.taskViewer(task);row.onkeydown=event=>{if(event.target===row&&(event.key==="Enter"||event.key===" "))this.taskViewer(task);};const actions=row.querySelector(".row-action-toggle");if(actions)actions.onclick=event=>{event.stopPropagation();this.actionMenu(actions,()=>this.taskEditor(task.group_id,task),()=>this.deleteTask(task));};});
    const add=root.querySelector(".add-task");if(add)add.onclick=()=>this.taskEditor(null);
  }
}

export class HomeTaskerCardEditor extends HTMLElement {
  constructor(){super();this.attachShadow({mode:"open"});this.config={...DEFAULT_CARD_CONFIG};this.groups=[];this.users=[];this.loaded=false;}
  set hass(value){this._hass=value;if(!this.loaded){this.loaded=true;this.load();}}
  setConfig(config){this.config=normalizeCardConfig(config);this.render();}
  async load(){try{const data=await this._hass.connection.sendMessagePromise({type:"home_tasker/list"});this.groups=data.groups||[];this.users=data.users||[];}catch(error){console.error("Home Tasker card editor load failed",error);}this.render();}
  update(patch){this.config=normalizeCardConfig({...this.config,...patch});this.dispatchEvent(new CustomEvent("config-changed",{detail:{config:{...this.config}},bubbles:true,composed:true}));this.render();}
  checks(items,selected,name){return items.map(item=>`<label><input type="checkbox" name="${name}" value="${esc(item.id)}" ${selected.includes(item.id)?"checked":""}><span>${esc(item.name)}</span></label>`).join("");}
  render(){if(!this.shadowRoot)return;this.shadowRoot.innerHTML=`<style>:host{display:block}.editor{display:grid;gap:16px}.field{display:grid;gap:7px}.choices{display:grid;gap:6px;max-height:180px;overflow:auto;padding:8px;border:1px solid var(--divider-color);border-radius:8px}.choices label,.toggle{display:flex;gap:8px;align-items:center}select,input[type=number]{box-sizing:border-box;width:100%;padding:9px;border:1px solid var(--divider-color);border-radius:8px;background:var(--card-background-color);color:var(--primary-text-color)}</style><div class="editor"><label class="field"><span>Modus</span><select name="mode"><option value="view" ${this.config.mode==="view"?"selected":""}>Anzeigen</option><option value="edit" ${this.config.mode==="edit"?"selected":""}>Bearbeiten</option></select></label><label class="toggle"><input name="hide_card_background" type="checkbox" ${this.config.hide_card_background?"checked":""}><span>Hintergrund und Rahmen ausblenden</span></label><label class="field"><span>Tage in die Zukunft (leer = alle)</span><input name="due_days" type="number" min="0" step="1" value="${this.config.due_days??""}"></label><div class="field"><span>Gruppen (keine Auswahl = alle)</span><div class="choices groups">${this.checks(this.groups,this.config.group_ids,"groups")||"Keine Gruppen vorhanden"}</div></div><div class="field"><span>Benutzer (keine Auswahl = alle)</span><div class="choices users">${this.checks([{id:UNASSIGNED,name:"Nicht zugewiesen"},...this.users],this.config.assignee_user_ids,"users")}</div></div></div>`;
    this.shadowRoot.querySelector('[name="mode"]').onchange=event=>this.update({mode:event.target.value});this.shadowRoot.querySelector('[name="hide_card_background"]').onchange=event=>this.update({hide_card_background:event.target.checked});this.shadowRoot.querySelector('[name="due_days"]').onchange=event=>this.update({due_days:event.target.value===""?null:Math.max(0,Math.trunc(Number(event.target.value)||0))});for(const [selector,key] of [[".groups","group_ids"],[".users","assignee_user_ids"]])this.shadowRoot.querySelector(selector).onchange=()=>this.update({[key]:[...this.shadowRoot.querySelectorAll(`${selector} input:checked`)].map(input=>input.value)});
  }
}

if(!customElements.get("home-tasker-card"))customElements.define("home-tasker-card",HomeTaskerCard);
if(!customElements.get("home-tasker-card-editor"))customElements.define("home-tasker-card-editor",HomeTaskerCardEditor);
window.customCards=window.customCards||[];
if(!window.customCards.some(card=>card.type==="home-tasker-card"))window.customCards.push({type:"home-tasker-card",name:"Home Tasker",description:"Fällige Home-Tasker-Aufgaben als flache Liste"});
