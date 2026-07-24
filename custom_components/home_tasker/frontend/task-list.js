import { t } from "./localize.js";
import { createActionMenu } from "./action-menu.js";

export const NO_DUE_TIMESTAMP = Number.MAX_SAFE_INTEGER;
export const INITIAL_TASK_SORTING = {column:"due_ts",direction:"asc"};
export const DEFAULT_TASK_COLUMN_ORDER = ["name","due_ts","assignee","nfc_tag","files","labels","actions","recurrence","rhythm"];
export const DEFAULT_HIDDEN_TASK_COLUMNS = ["recurrence","rhythm"];
export const TASK_GROUP_COLUMNS = ["labels","recurrence","rhythm","assignee"];
export const TASK_FILTER_COLUMNS = ["labels","assignee","recurrence","rhythm"];
export const FILTER_CATEGORY_TAG="home-tasker-filter-category";

export class HomeTaskerFilterCategory extends HTMLElement {
  constructor(){super();this.attachShadow({mode:"open"});this._items=[];this._value=[];this.expanded=false;this.label="";this.icon="mdi:filter-variant";}
  set items(value){this._items=Array.isArray(value)?value:[];this.render();}
  get items(){return this._items;}
  set value(value){this._value=Array.isArray(value)?value:[];this.render();}
  get value(){return this._value;}
  connectedCallback(){this.render();}
  select(id){this._value=id?(this._value.includes(id)?this._value.filter(value=>value!==id):[...this._value,id]):[];this.dispatchEvent(new CustomEvent("value-changed",{bubbles:true,composed:true,detail:{value:this._value}}));this.render();}
  render(){
    if(!this.shadowRoot)return;
    this.shadowRoot.innerHTML=`<style>:host{display:block;border-bottom:1px solid var(--divider-color)}ha-expansion-panel{--ha-card-border-radius:var(--ha-border-radius-square);--expansion-panel-content-padding:0}.header{display:flex;align-items:center}.badge{display:inline-block;box-sizing:border-box;min-width:16px;margin-inline-start:8px;padding:0 2px;border-radius:var(--ha-border-radius-circle);background:var(--primary-color);color:var(--text-primary-color);font-size:var(--ha-font-size-xs);font-weight:var(--ha-font-weight-normal);line-height:var(--ha-line-height-normal);text-align:center}ha-list{--mdc-list-item-meta-size:auto;--mdc-list-side-padding-right:var(--ha-space-1);--mdc-list-side-padding-left:var(--ha-space-4);--ha-icon-button-size:36px}ha-list-item{--mdc-list-item-graphic-margin:var(--ha-space-4)}ha-dropdown-item{font-size:var(--ha-font-size-m)}</style><ha-expansion-panel left-chevron><div slot="header" class="header">${this.label}${this._value.length?`<span class="badge">${this._value.length}</span>`:""}</div><ha-list activatable></ha-list></ha-expansion-panel>`;
    const panel=this.shadowRoot.querySelector("ha-expansion-panel"),list=this.shadowRoot.querySelector("ha-list");panel.expanded=this.expanded;panel.addEventListener("expanded-changed",event=>{this.expanded=Boolean(event.detail?.expanded);});
    const all=document.createElement("ha-list-item");all.textContent=t("filter.show_all");all.selected=!this._value.length;all.activated=!this._value.length;all.addEventListener("click",()=>this.select(null));list.append(all);
    for(const option of this._items){const item=document.createElement("ha-list-item"),icon=document.createElement("ha-icon");item.value=option.value;item.selected=this._value.includes(option.value);item.activated=item.selected;item.graphic="icon";icon.slot="graphic";icon.setAttribute("icon",this.icon);item.append(icon,document.createTextNode(option.label));item.addEventListener("click",()=>this.select(option.value));list.append(item);}
  }
}

if(!customElements.get(FILTER_CATEGORY_TAG))customElements.define(FILTER_CATEGORY_TAG,HomeTaskerFilterCategory);

export function dueTimestamp(value) {
  const text=String(value||""),match=/^(\d{4})-(\d{2})-(\d{2})$/.exec(text);
  if(text.includes("T")){const timestamp=Date.parse(text);return Number.isNaN(timestamp)?NO_DUE_TIMESTAMP:timestamp;}
  if(!match)return NO_DUE_TIMESTAMP;
  const year=Number(match[1]),month=Number(match[2]),day=Number(match[3]),date=new Date(year,month-1,day);
  return date.getFullYear()===year&&date.getMonth()===month-1&&date.getDate()===day?date.getTime():NO_DUE_TIMESTAMP;
}

export function taskTableRows(tasks,{users=[],tags=[],labels=[],attachments=[],translate=t}={}) {
  const userNames=new Map(users.map(user=>[user.id,user.name]));
  const tagNames=new Map(tags.map(tag=>[tag.id,tag.name]));
  const labelNames=new Map(labels.map(label=>[label.label_id,label.name]));
  const fileCounts=new Map();
  for(const file of attachments)fileCounts.set(file.task_id,(fileCounts.get(file.task_id)||0)+1);
  return tasks.map(task=>{
    const schedule_unit=["daily","weekly","monthly","yearly"].includes(task.schedule_unit)?task.schedule_unit:"monthly";
    return {
      id:task.task_id,
      task,
      name:task.task_name||"",
      due_ts:dueTimestamp(task.task_due),
      recurrence:translate(`task.${task.schedule_type==="fixed"?"fixed":"sliding"}`),
      rhythm:translate(`task.${schedule_unit}`),
      assignee:userNames.get(task.assignee_id)||task.assignee_id||translate("task.unassigned"),
      labels:(task.label_ids||[]).map(id=>labelNames.get(id)||id).sort((a,b)=>a.localeCompare(b)).join(", ")||translate("task.no_labels"),
      label_names:(task.label_ids||[]).map(id=>labelNames.get(id)||id),
      nfc_tag:tagNames.get(task.nfc_tag_id)||task.nfc_tag_id||translate("task.no_nfc_tag"),
      files:fileCounts.get(task.task_id)||0,
    };
  });
}

export function filterTaskTableRows(rows,filters={}) {
  return rows.filter(row=>TASK_FILTER_COLUMNS.every(column=>!filters[column]?.length||(column==="labels"?filters.labels.some(label=>row.label_names.includes(label)):filters[column].includes(row[column]))));
}

function textCell(value,title) {
  const cell=document.createElement("span");
  cell.textContent=value;
  if(title)cell.title=title;
  return cell;
}

function dropdownItem(value,label,icon,slot="") {
  const item=document.createElement("ha-dropdown-item");
  item.value=value;
  item.textContent=label;
  if(slot)item.slot=slot;
  if(icon){const itemIcon=document.createElement("ha-icon");itemIcon.slot="icon";itemIcon.setAttribute("icon",icon);item.prepend(itemIcon);}
  return item;
}

function bulkDropdown(label,items,action) {
  const dropdown=document.createElement("ha-dropdown"),trigger=document.createElement("ha-assist-chip"),chevron=document.createElement("ha-icon");
  dropdown.slot="selection-bar";
  trigger.slot="trigger";
  trigger.label=label;
  chevron.slot="trailing-icon";
  chevron.setAttribute("icon","mdi:menu-down");
  trigger.append(chevron);
  dropdown.append(trigger,...items);
  dropdown.addEventListener("wa-select",event=>{const item=event.detail?.item,value=item?.value;if(value!==undefined)void action(value,item);});
  return dropdown;
}

function overflowDropdown(label,items,action,narrow=false) {
  const dropdown=document.createElement("ha-dropdown"),trigger=narrow?document.createElement("ha-assist-chip"):document.createElement("ha-icon-button"),icon=document.createElement("ha-icon");
  dropdown.slot="selection-bar";
  trigger.slot="trigger";
  trigger.label=label;
  if(narrow){icon.slot="trailing-icon";icon.setAttribute("icon","mdi:menu-down");trigger.append(icon);}else{trigger.title=label;trigger.setAttribute("aria-label",label);icon.setAttribute("icon","mdi:dots-vertical");trigger.append(icon);}
  dropdown.append(trigger,...items);
  dropdown.addEventListener("wa-select",event=>{const item=event.detail?.item,value=item?.value;if(value!==undefined)void action(value,item);});
  return dropdown;
}

export const withTaskList = Base => class extends Base {
  tagName(task){const id=task?.nfc_tag_id;return id?(this.tags?.find(tag=>tag.id===id)?.name||id):"";}
  tableRows(){return taskTableRows(this.tasks,{users:this.users,tags:this.tags,labels:this.labels,attachments:this.attachments,translate:t});}
  filterLabel(schema){return {labels:t("task.labels"),assignee:t("table.assignee"),recurrence:t("table.recurrence"),rhythm:t("table.rhythm")}[schema.name]||schema.name;}
  filterItems(rows,column){return [...new Set(rows.flatMap(row=>column==="labels"?row.label_names:row[column]))].map(value=>({value,label:value}));}
  activeFilterCount(){return TASK_FILTER_COLUMNS.reduce((count,column)=>count+(this.tableFilters?.[column]?.length||0),0);}
  tableColumns(){
    const groupable={sortable:true,filterable:true,groupable:true};
    return {
      name:{title:t("table.task"),main:true,sortable:true,filterable:true,flex:3},
      due_ts:{title:t("task.due"),sortable:true,filterable:false,template:row=>textCell(row.task.task_due?this.relativeDate(row.task.task_due):"–",row.task.task_due?this.date(row.task.task_due):"")},
      assignee:{title:t("table.assignee"),...groupable},
      labels:{title:t("table.label"),...groupable},
      nfc_tag:{title:t("task.nfc_tag_id"),sortable:true,filterable:true},
      files:{title:t("task.files"),sortable:true,filterable:false},
      recurrence:{title:t("table.recurrence"),defaultHidden:true,...groupable},
      rhythm:{title:t("table.rhythm"),defaultHidden:true,...groupable},
      actions:{title:"",label:t("task.actions"),type:"overflow-menu",moveable:false,hideable:false,showNarrow:true,template:row=>this.taskActionButton(row.task)},
    };
  }
  taskActionButton(task){
    return createActionMenu({
      label:t("task.actions"),
      edit:()=>this.taskEditor(task),
      remove:()=>this.deleteTask(task),
    });
  }
  selectedTasks(){const ids=new Set(this.selectedTaskIds||[]);return this.tasks.filter(task=>ids.has(task.task_id));}
  clearTaskSelection(){const wrapper=this.shadowRoot.querySelector("hass-tabs-subpage-data-table");wrapper?.clearSelection();this.selectedTaskIds=[];if(wrapper)wrapper.selected=0;}
  async runBulkAction(action,clear=false){for(const task of this.selectedTasks())await action(task);if(clear)this.clearTaskSelection();}
  async bulkAssignPerson(assigneeId){await this.runBulkAction(task=>this.ws({type:"home_tasker/task/update",task_id:task.task_id,assignee_id:assigneeId==="__unassigned__"?null:assigneeId}));}
  async bulkAssignLabel(labelId,action="add"){await this.runBulkAction(task=>this.ws({type:"home_tasker/task/update",task_id:task.task_id,label_ids:action==="remove"?(task.label_ids||[]).filter(id=>id!==labelId):[...new Set([...(task.label_ids||[]),labelId])]}));}
  async bulkComplete(){const tasks=this.selectedTasks();if(!tasks.length||!await this.confirmAction(t("bulk.complete_title"),t("bulk.complete_confirm",{count:tasks.length}),t("task.completed"),"brand"))return;await this.runBulkAction(task=>this.ws({type:"home_tasker/task/complete",task_id:task.task_id,notes:null}));}
  async bulkDelete(){const tasks=this.selectedTasks();if(!tasks.length||!await this.confirmAction(t("bulk.delete_title"),t("bulk.delete_confirm",{count:tasks.length}),t("common.delete"),"danger"))return;await this.runBulkAction(task=>this.ws({type:"home_tasker/task/delete",task_id:task.task_id}),true);}
  personItems(slot=""){return [["__unassigned__",t("task.unassigned"),"mdi:account-off-outline"],...this.users.map(user=>[user.id,user.name,"mdi:account"])].map(([value,label,icon])=>dropdownItem(`person_${value}`,label,icon,slot));}
  labelItems(slot=""){const tasks=this.selectedTasks();return this.labels.map(label=>{const selected=tasks.length>0&&tasks.every(task=>(task.label_ids||[]).includes(label.label_id)),partial=!selected&&tasks.some(task=>(task.label_ids||[]).includes(label.label_id)),item=dropdownItem(`label_${label.label_id}`,"",null,slot),checkbox=document.createElement("ha-checkbox"),display=document.createElement("ha-label");item.dataset.action=selected?"remove":"add";item.setAttribute("keep-open","");checkbox.slot="icon";checkbox.checked=selected;checkbox.indeterminate=partial;display.color=label.color;display.description=label.description||undefined;display.textContent=label.name;if(label.icon){const icon=document.createElement("ha-icon");icon.slot="icon";icon.setAttribute("icon",label.icon);display.prepend(icon);}item.append(checkbox,display);return item;});}
  handleBulkMenu(value,item){if(value==="complete")void this.bulkComplete();else if(value==="delete")void this.bulkDelete();else if(value==="person_menu"||value==="label_menu")return;else if(value.startsWith("person_"))void this.bulkAssignPerson(value.slice(7));else if(value.startsWith("label_"))void this.bulkAssignLabel(value.slice(6),item.dataset.action);}
  selectionSubmenu(label,value,items){const parent=dropdownItem(value,label);for(const item of items){item.slot="submenu";parent.append(item);}return parent;}
  refreshTableWidth(wrapper){requestAnimationFrame(()=>requestAnimationFrame(()=>{const table=wrapper.shadowRoot?.querySelector("ha-data-table");table?.style.removeProperty("--table-row-width");table?.requestUpdate?.();}));}
  filterToggleClicked(event,wrapper){const label=this._hass?.localize?.("ui.components.subpage-data-table.filters");if(event.composedPath().some(element=>element?.localName==="ha-assist-chip"&&element.label===label))this.refreshTableWidth(wrapper);}
  appendBulkActions(wrapper){
    wrapper.querySelectorAll('[slot="selection-bar"]').forEach(element=>element.remove());
    const complete=dropdownItem("complete",t("bulk.complete"),"mdi:check-circle-outline"),remove=dropdownItem("delete",t("bulk.delete"),"mdi:delete-outline");remove.setAttribute("variant","danger");
    if(this.narrow){wrapper.append(overflowDropdown(t("bulk.actions"),[this.selectionSubmenu(t("bulk.assign_person"),"person_menu",this.personItems("submenu")),this.selectionSubmenu(t("bulk.assign_label"),"label_menu",this.labelItems("submenu")),document.createElement("wa-divider"),complete,remove],(value,item)=>this.handleBulkMenu(value,item),true));return;}
    wrapper.append(
      bulkDropdown(t("bulk.assign_person"),this.personItems(),(value,item)=>this.handleBulkMenu(value,item)),
      bulkDropdown(t("bulk.assign_label"),this.labelItems(),(value,item)=>this.handleBulkMenu(value,item)),
      overflowDropdown(t("bulk.actions"),[complete,remove],(value,item)=>this.handleBulkMenu(value,item)),
    );
  }
  render(){
    if(!this.shadowRoot.querySelector(".app")){
      this.shadowRoot.innerHTML=`<style>:host{display:block;height:100%;background:var(--primary-background-color);color:var(--primary-text-color)}.app,hass-tabs-subpage-data-table{display:block;height:100%}.filters{box-sizing:border-box;width:100%}ha-assist-chip{--ha-assist-chip-container-shape:10px}</style><div class="app"></div>`;
      const wrapper=document.createElement("hass-tabs-subpage-data-table"),settings=document.createElement("ha-icon-button"),settingsIcon=document.createElement("ha-icon"),filterPane=document.createElement("div"),fab=document.createElement("ha-button"),fabIcon=document.createElement("ha-icon");
      wrapper.className="task-table";
      wrapper.mainPage=true;
      wrapper.style.width="100%";
      wrapper.style.setProperty("--main-title-margin","0");
      wrapper.setAttribute("clickable","");
      wrapper.setAttribute("selectable","");
      wrapper.setAttribute("has-fab","");
      wrapper.setAttribute("has-filters","");
      wrapper.columnOrder=[...DEFAULT_TASK_COLUMN_ORDER];
      wrapper.hiddenColumns=[...DEFAULT_HIDDEN_TASK_COLUMNS];
      settings.slot="toolbar-icon";
      settings.label=t("settings.title");
      settings.setAttribute("aria-label",t("settings.title"));
      settingsIcon.setAttribute("icon","mdi:cog-outline");
      settings.append(settingsIcon);
      settings.addEventListener("click",event=>{event.stopPropagation();this.settings();});
      filterPane.className="filters";filterPane.slot="filter-pane";for(const column of TASK_FILTER_COLUMNS){const filter=document.createElement("home-tasker-filter-category");filter.dataset.column=column;filter.controller=this;filter.addEventListener("value-changed",event=>{event.stopPropagation();this.tableFilters={...(this.tableFilters||{}),[column]:event.detail?.value||[]};this.updateTaskTable();});filterPane.append(filter);}
      fab.slot="fab";
      fab.setAttribute("size","l");
      fab.textContent=t("common.add_task");
      fabIcon.slot="start";
      fabIcon.setAttribute("icon","mdi:plus");
      fab.prepend(fabIcon);
      fab.addEventListener("click",()=>this.taskEditor(null));
      wrapper.append(settings,filterPane,fab);
      this.appendBulkActions(wrapper);
      this.shadowRoot.querySelector(".app").append(wrapper);
      wrapper.addEventListener("click",event=>this.filterToggleClicked(event,wrapper));
      wrapper.addEventListener("selection-changed",event=>{this.selectedTaskIds=event.detail?.value||[];wrapper.selected=this.selectedTaskIds.length;this.appendBulkActions(wrapper);});
      wrapper.addEventListener("row-click",event=>{const task=this.tasks.find(item=>item.task_id===event.detail?.id);if(task)this.taskViewer(task);});
      wrapper.addEventListener("clear-filter",()=>{this.tableFilters={};this.updateTaskTable();});
    }
    this.updateTaskTable();
  }
  updateTaskTable(){
    const wrapper=this.shadowRoot.querySelector("hass-tabs-subpage-data-table");
    if(!wrapper)return;
    const settings=wrapper.querySelector('[slot="toolbar-icon"]'),fab=wrapper.querySelector('[slot="fab"]'),rows=this.tableRows();
    if(settings){settings.label=t("settings.title");settings.title=t("settings.title");settings.setAttribute("aria-label",t("settings.title"));}
    if(fab){for(const node of [...fab.childNodes])if(node.nodeType===3)node.remove();fab.append(document.createTextNode(t("common.add_task")));}
    wrapper.querySelectorAll("home-tasker-filter-category").forEach(filter=>{const column=filter.dataset.column;filter.controller=this;filter.label=this.filterLabel({name:column});filter.icon={labels:"mdi:label-outline",assignee:"mdi:account",recurrence:"mdi:calendar-sync",rhythm:"mdi:repeat"}[column];filter.items=this.filterItems(rows,column);filter.value=this.tableFilters?.[column]||[];});
    wrapper.hass=this._hass;
    wrapper.route=this.route;
    wrapper.tabs=[{name:"Home Tasker",path:""}];
    wrapper.narrow=Boolean(this.narrow);
    wrapper.isWide=Boolean(this.isWide);
    wrapper.columns=this.tableColumns();
    wrapper.data=filterTaskTableRows(rows,this.tableFilters);
    wrapper.selected=(this.selectedTaskIds||[]).length;
    this.appendBulkActions(wrapper);
    wrapper.filters=this.activeFilterCount();
    wrapper.noDataText=t("table.empty");
    wrapper.searchLabel=t("table.search");
    wrapper.initialSorting=INITIAL_TASK_SORTING;
  }
};
