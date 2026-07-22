import { t } from "./localize.js";
import { createActionMenu } from "./action-menu.js";
import "./filter-category.js";

export const NO_DUE_TIMESTAMP = Number.MAX_SAFE_INTEGER;
export const INITIAL_TASK_SORTING = {column:"due_ts",direction:"asc"};
export const DEFAULT_TASK_COLUMN_ORDER = ["name","due_ts","assignee","group","nfc_tag","files","actions","recurrence","rhythm"];
export const DEFAULT_HIDDEN_TASK_COLUMNS = ["recurrence","rhythm"];
export const TASK_GROUP_COLUMNS = ["recurrence","rhythm","group","assignee"];
export const TASK_FILTER_COLUMNS = ["group","assignee","recurrence","rhythm"];

export function dueTimestamp(value) {
  const match=/^(\d{4})-(\d{2})-(\d{2})$/.exec(String(value||""));
  if(!match)return NO_DUE_TIMESTAMP;
  const year=Number(match[1]),month=Number(match[2]),day=Number(match[3]),date=new Date(year,month-1,day);
  return date.getFullYear()===year&&date.getMonth()===month-1&&date.getDate()===day?date.getTime():NO_DUE_TIMESTAMP;
}

export function taskTableRows(tasks,{groups=[],users=[],tags=[],attachments=[],translate=t}={}) {
  const groupNames=new Map(groups.map(group=>[group.id,group.name]));
  const userNames=new Map(users.map(user=>[user.id,user.name]));
  const tagNames=new Map(tags.map(tag=>[tag.id,tag.name]));
  const fileCounts=new Map();
  for(const file of attachments)fileCounts.set(file.task_id,(fileCounts.get(file.task_id)||0)+1);
  return tasks.map(task=>{
    const frequency=["daily","weekly","monthly","yearly"].includes(task.frequency)?task.frequency:"monthly";
    return {
      id:task.id,
      task,
      name:task.name||"",
      due_ts:dueTimestamp(task.due_date),
      recurrence:translate(`task.${task.recurrence_mode==="fixed"?"fixed":"sliding"}`),
      rhythm:translate(`task.${frequency}`),
      group:groupNames.get(task.group_id)||task.group_id||translate("task.no_group"),
      assignee:userNames.get(task.assignee_user_id)||task.assignee_user_id||translate("task.unassigned"),
      nfc_tag:tagNames.get(task.nfc_tag_id)||task.nfc_tag_id||translate("task.no_nfc_tag"),
      files:fileCounts.get(task.id)||0,
    };
  });
}

export function filterTaskTableRows(rows,filters={}) {
  return rows.filter(row=>TASK_FILTER_COLUMNS.every(column=>!filters[column]?.length||filters[column].includes(row[column])));
}

function textCell(value,title) {
  const cell=document.createElement("span");
  cell.textContent=value;
  if(title)cell.title=title;
  return cell;
}

export const withTaskList = Base => class extends Base {
  tagName(task){const id=task?.nfc_tag_id;return id?(this.tags?.find(tag=>tag.id===id)?.name||id):"";}
  tableRows(){return taskTableRows(this.tasks,{groups:this.groups,users:this.users,tags:this.tags,attachments:this.attachments,translate:t});}
  filterLabel(schema){return {group:t("task.group"),assignee:t("table.assignee"),recurrence:t("table.recurrence"),rhythm:t("table.rhythm")}[schema.name]||schema.name;}
  filterItems(rows,column){return column==="group"?this.groups.map(group=>({value:group.name,label:group.name,source:group})):[...new Set(rows.map(row=>row[column]))].map(value=>({value,label:value}));}
  activeFilterCount(){return TASK_FILTER_COLUMNS.reduce((count,column)=>count+(this.tableFilters?.[column]?.length||0),0);}
  tableColumns(){
    const groupable={sortable:true,filterable:true,groupable:true};
    return {
      name:{title:t("table.task"),main:true,sortable:true,filterable:true,flex:3},
      due_ts:{title:t("task.due"),sortable:true,filterable:false,template:row=>textCell(row.task.due_date?this.relativeDate(row.task.due_date):"–",row.task.due_date?this.date(row.task.due_date):"")},
      assignee:{title:t("table.assignee"),...groupable},
      group:{title:t("task.group"),...groupable},
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
      edit:()=>this.taskEditor(task.group_id,task),
      remove:()=>this.deleteTask(task),
    });
  }
  render(){
    if(!this.shadowRoot.querySelector(".app")){
      this.shadowRoot.innerHTML=`<style>:host{display:block;height:100%;background:var(--primary-background-color);color:var(--primary-text-color)}.app,hass-tabs-subpage-data-table{display:block;height:100%}.filters{box-sizing:border-box;width:100%}</style><div class="app"></div>`;
      const wrapper=document.createElement("hass-tabs-subpage-data-table"),settings=document.createElement("ha-icon-button"),settingsIcon=document.createElement("ha-icon"),filterPane=document.createElement("div"),fab=document.createElement("ha-button"),fabIcon=document.createElement("ha-icon");
      wrapper.className="task-table";
      wrapper.setAttribute("main-page","");
      wrapper.setAttribute("clickable","");
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
      this.shadowRoot.querySelector(".app").append(wrapper);
      wrapper.addEventListener("row-click",event=>{const task=this.tasks.find(item=>item.id===event.detail?.id);if(task)this.taskViewer(task);});
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
    wrapper.querySelectorAll("home-tasker-filter-category").forEach(filter=>{const column=filter.dataset.column;filter.controller=this;filter.label=this.filterLabel({name:column});filter.icon={group:"mdi:devices",assignee:"mdi:account",recurrence:"mdi:calendar-sync",rhythm:"mdi:repeat"}[column];filter.actions=column==="group";filter.items=this.filterItems(rows,column);filter.value=this.tableFilters?.[column]||[];});
    wrapper.hass=this._hass;
    wrapper.route=this.route;
    wrapper.tabs=[{name:"Home Tasker",path:""}];
    wrapper.narrow=Boolean(this.narrow);
    wrapper.isWide=Boolean(this.isWide);
    wrapper.columns=this.tableColumns();
    wrapper.data=filterTaskTableRows(rows,this.tableFilters);
    wrapper.filters=this.activeFilterCount();
    wrapper.noDataText=t("table.empty");
    wrapper.searchLabel=t("table.search");
    wrapper.initialSorting=INITIAL_TASK_SORTING;
  }
};
