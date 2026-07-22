import { HomeTaskerBase } from "./main.js";
import { esc } from "./shared.js";
import { createActionMenu } from "./action-menu.js";
import { ready, setLanguage, t } from "./localize.js";

export const UNASSIGNED = "__unassigned__";
export const DEFAULT_CARD_CONFIG = Object.freeze({
  type: "custom:home-tasker-card",
  mode: "view",
  due_days: 0,
  group_ids: [],
  assignee_user_ids: [],
});

export function normalizeCardConfig(config={}) {
  const supportedConfig={...config};
  delete supportedConfig.sort_direction;
  delete supportedConfig.hide_card_background;
  const dueDays=config.due_days===null?null:Number.isInteger(Number(config.due_days))&&Number(config.due_days)>=0?Number(config.due_days):0;
  return {
    ...DEFAULT_CARD_CONFIG,
    ...supportedConfig,
    mode:config.mode==="edit"?"edit":"view",
    due_days:dueDays,
    group_ids:Array.isArray(config.group_ids)?[...config.group_ids]:[],
    assignee_user_ids:Array.isArray(config.assignee_user_ids)?[...config.assignee_user_ids]:[],
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

export function sortDashboardTasks(tasks,locale="en"){
  return [...tasks].sort((a,b)=>(a.due_date||"").localeCompare(b.due_date||"")||(a.name||"").localeCompare(b.name||"",locale));
}

export function dueStatus(dueDate,today){return dueDate<today?"overdue":dueDate===today?"today":"future";}
export function dashboardTaskRowHtml(task,editable,relativeDate,status,assigneeName="",tagName=""){return `<div class="task-row${editable?" editable":""}" data-task="${esc(task.id)}" tabindex="0"><div><div class="task-name">${esc(task.name)}</div><div class="pills"><span class="pill due-date ${esc(status)}">${esc(relativeDate)}</span>${assigneeName?`<span class="pill"><ha-icon icon="mdi:account"></ha-icon>${esc(assigneeName)}</span>`:""}${tagName?`<span class="pill"><ha-icon icon="mdi:nfc"></ha-icon>${esc(tagName)}</span>`:""}</div></div>${editable?'<span class="row-action-slot"></span>':""}</div>`;}
export function dashboardCardBodyHtml(rows,editable){return `<ha-card style="--ha-card-border-width:0px;--ha-card-border-color:transparent;border:none!important;background:transparent!important;box-shadow:none!important"><div class="card-content">${editable?`<ha-button class="add-task" appearance="plain"><ha-icon slot="start" icon="mdi:plus"></ha-icon>${t("card.add")}</ha-button>`:""}${rows||`<div class="empty">${t("card.empty")}</div>`}</div></ha-card>`;}
export function canEditCard(config){return normalizeCardConfig(config).mode==="edit";}

export class HomeTaskerCard extends HomeTaskerBase {
  static getStubConfig(){return {...DEFAULT_CARD_CONFIG};}
  static async getConfigElement(){return document.createElement("home-tasker-card-editor");}
  setConfig(config){this.config=normalizeCardConfig(config);if(this.loaded)this.render();}
  getCardSize(){return Math.max(1,Math.min(8,this.visibleTasks().length+1));}
  visibleTasks(){return sortDashboardTasks(filterDashboardTasks(this.tasks||[],this.config||DEFAULT_CARD_CONFIG,this.today),this.locale());}
  render(){
    if(!this.shadowRoot.querySelector(".card-root"))this.shadowRoot.innerHTML=`${this.styles()}<style>:host{display:block}ha-card{overflow:hidden}.card-content{display:grid;gap:8px;padding:0}.task-row{display:grid;grid-template-columns:minmax(0,1fr);align-items:center;min-height:52px;padding:4px 12px;border:1px solid var(--ha-card-border-color,var(--divider-color));border-radius:var(--ha-card-border-radius,12px);background:var(--ha-card-background,var(--card-background-color));cursor:pointer;transition:background-color 180ms ease-in-out}.task-row:hover{background:var(--secondary-background-color)}.task-row.editable{grid-template-columns:minmax(0,1fr) 44px}.task-name{font-weight:var(--ha-font-weight-normal,400)}.pills{display:flex;gap:6px;flex-wrap:wrap;align-items:center;margin-top:4px}.due-date.today{color:var(--warning-color,#f57c00)}.due-date.overdue{color:var(--error-color,#d32f2f)}.due-date.future{color:var(--success-color,#43a047)}.empty{padding:20px;color:var(--secondary-text-color);text-align:center}.add-task{width:100%}</style><div class="card-root"></div>`;
    const root=this.shadowRoot.querySelector(".card-root"),tasks=this.visibleTasks(),editable=canEditCard(this.config);
    root.innerHTML=dashboardCardBodyHtml(tasks.map(task=>dashboardTaskRowHtml(task,editable,this.relativeDate(task.due_date),dueStatus(task.due_date,this.today),this.users.find(user=>user.id===task.assignee_user_id)?.name||"",this.tagName(task))).join(""),editable);
    root.insertAdjacentHTML("beforeend",'<style>.task-row{border-color:var(--divider-color)}</style>'+this.themeStyles()+this.pillStyles());
    root.querySelectorAll("[data-task]").forEach(row=>{const task=this.tasks.find(item=>item.id===row.dataset.task);row.onclick=()=>this.taskViewer(task);row.onkeydown=event=>{if(event.target===row&&(event.key==="Enter"||event.key===" "))this.taskViewer(task);};const slot=row.querySelector(".row-action-slot");if(slot)slot.replaceWith(createActionMenu({label:t("task.actions"),edit:()=>this.taskEditor(task.group_id,task),remove:()=>this.deleteTask(task)}));});
    const add=root.querySelector(".add-task");if(add)add.onclick=()=>this.taskEditor(null);
  }
}

export class HomeTaskerCardEditor extends HTMLElement {
  constructor(){super();this.attachShadow({mode:"open"});this.config={...DEFAULT_CARD_CONFIG};this.groups=[];this.users=[];this.loaded=false;}
  set hass(value){this._hass=value;setLanguage(value?.locale?.language).then(changed=>{updateCardMetadata();if(!this.loaded){this.loaded=true;this.load();}else if(changed)this.render();});}
  setConfig(config){this.config=normalizeCardConfig(config);this.render();}
  async load(){try{const data=await this._hass.connection.sendMessagePromise({type:"home_tasker/list"});this.groups=data.groups||[];this.users=data.users||[];}catch(error){console.error("Home Tasker card editor load failed",error);}this.render();}
  update(patch){this.config=normalizeCardConfig({...this.config,...patch});this.dispatchEvent(new CustomEvent("config-changed",{detail:{config:{...this.config}},bubbles:true,composed:true}));this.render();}
  checks(items,selected,name){return items.map(item=>`<label><input type="checkbox" name="${name}" value="${esc(item.id)}" ${selected.includes(item.id)?"checked":""}><span>${esc(item.name)}</span></label>`).join("");}
  render(){if(!this.shadowRoot)return;this.shadowRoot.innerHTML=`<style>:host{display:block}.editor{display:grid;gap:16px}.field{display:grid;gap:7px}.choices{display:grid;gap:6px;max-height:180px;overflow:auto;padding:8px;border:1px solid var(--divider-color);border-radius:8px}.choices label{display:flex;gap:8px;align-items:center}select,input[type=number]{box-sizing:border-box;width:100%;padding:9px;border:1px solid var(--divider-color);border-radius:8px;background:var(--card-background-color);color:var(--primary-text-color)}</style><div class="editor"><label class="field"><span>${t("card.mode")}</span><select name="mode"><option value="view" ${this.config.mode==="view"?"selected":""}>${t("card.mode_view")}</option><option value="edit" ${this.config.mode==="edit"?"selected":""}>${t("card.mode_edit")}</option></select></label><label class="field"><span>${t("card.due_days")}</span><input name="due_days" type="number" min="0" step="1" value="${this.config.due_days??""}"></label><div class="field"><span>${t("card.groups")}</span><div class="choices groups">${this.checks(this.groups,this.config.group_ids,"groups")||t("group.none")}</div></div><div class="field"><span>${t("card.users")}</span><div class="choices users">${this.checks([{id:UNASSIGNED,name:t("task.unassigned")},...this.users],this.config.assignee_user_ids,"users")}</div></div></div>`;
    this.shadowRoot.querySelector('[name="mode"]').onchange=event=>this.update({mode:event.target.value});this.shadowRoot.querySelector('[name="due_days"]').onchange=event=>this.update({due_days:event.target.value===""?null:Math.max(0,Math.trunc(Number(event.target.value)||0))});for(const [selector,key] of [[".groups","group_ids"],[".users","assignee_user_ids"]])this.shadowRoot.querySelector(selector).onchange=()=>this.update({[key]:[...this.shadowRoot.querySelectorAll(`${selector} input:checked`)].map(input=>input.value)});
  }
}

if(!customElements.get("home-tasker-card"))customElements.define("home-tasker-card",HomeTaskerCard);
if(!customElements.get("home-tasker-card-editor"))customElements.define("home-tasker-card-editor",HomeTaskerCardEditor);
window.customCards=window.customCards||[];
function updateCardMetadata(){const card=window.customCards.find(item=>item.type==="home-tasker-card");if(card)card.description=t("card.description");}
ready.then(()=>{if(!window.customCards.some(card=>card.type==="home-tasker-card"))window.customCards.push({type:"home-tasker-card",name:"Home Tasker",description:t("card.description")});else updateCardMetadata();});
