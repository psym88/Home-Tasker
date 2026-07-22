import { t } from "./localize.js";

export const NO_DUE_TIMESTAMP = Number.MAX_SAFE_INTEGER;
export const INITIAL_TASK_SORTING = {column:"due_ts",direction:"asc"};
export const TASK_GROUP_COLUMNS = ["recurrence","group","assignee"];
export const TASK_FILTER_COLUMNS = ["group","assignee","recurrence"];

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
      recurrence:translate(`task.${frequency}`),
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
  filterSchema(rows){return TASK_FILTER_COLUMNS.map(column=>({name:column,selector:{select:{multiple:true,mode:"dropdown",options:[...new Set(rows.map(row=>row[column]))].map(value=>({value,label:value}))}}}));}
  filterLabel(schema){return {group:t("task.group"),assignee:t("table.assignee"),recurrence:t("table.recurrence")}[schema.name]||schema.name;}
  activeFilterCount(){return TASK_FILTER_COLUMNS.reduce((count,column)=>count+(this.tableFilters?.[column]?.length||0),0);}
  tableColumns(){
    const groupable={sortable:true,filterable:true,groupable:true};
    return {
      name:{title:t("table.task"),main:true,sortable:true,filterable:true,flex:3},
      due_ts:{title:t("task.due"),sortable:true,filterable:false,template:row=>textCell(row.task.due_date?this.relativeDate(row.task.due_date):"–",row.task.due_date?this.date(row.task.due_date):"")},
      recurrence:{title:t("table.recurrence"),...groupable},
      group:{title:t("task.group"),...groupable},
      assignee:{title:t("table.assignee"),...groupable},
      nfc_tag:{title:t("task.nfc_tag_id"),sortable:true,filterable:true},
      files:{title:t("task.files"),sortable:true,filterable:false},
      actions:{title:"",label:t("task.actions"),type:"overflow-menu",moveable:false,hideable:false,showNarrow:true,template:row=>this.taskActionButton(row.task)},
    };
  }
  taskActionButton(task){
    const dropdown=document.createElement("ha-dropdown"),button=document.createElement("ha-icon-button"),icon=document.createElement("ha-icon"),edit=document.createElement("ha-dropdown-item"),remove=document.createElement("ha-dropdown-item"),stop=event=>event.stopPropagation();
    button.className="row-action-toggle";
    button.slot="trigger";
    button.label=t("task.actions");
    button.title=t("task.actions");
    button.setAttribute("aria-label",t("task.actions"));
    button.setAttribute("aria-haspopup","menu");
    button.setAttribute("aria-expanded","false");
    icon.setAttribute("icon","mdi:dots-vertical");
    button.append(icon);
    edit.value="edit";
    edit.innerHTML=`<ha-icon slot="icon" icon="mdi:pencil"></ha-icon>${t("menu.edit")}`;
    remove.value="delete";
    remove.innerHTML=`<ha-icon slot="icon" icon="mdi:delete"></ha-icon>${t("menu.delete")}`;
    dropdown.addEventListener("pointerdown",stop);
    dropdown.addEventListener("click",stop);
    dropdown.addEventListener("wa-select",event=>{
      event.stopPropagation();
      const action=event.detail?.item?.value;
      if(action==="edit")this.taskEditor(task.group_id,task);
      if(action==="delete")this.deleteTask(task);
    });
    dropdown.append(button,edit,remove);
    return dropdown;
  }
  render(){
    this.closeActionMenu();
    if(!this.shadowRoot.querySelector(".app")){
      this.shadowRoot.innerHTML=`<style>:host{display:block;height:100%;background:var(--primary-background-color);color:var(--primary-text-color)}.app,hass-tabs-subpage-data-table{display:block;height:100%}.filters{margin:16px}</style><div class="app"></div>`;
      const wrapper=document.createElement("hass-tabs-subpage-data-table"),settings=document.createElement("ha-icon-button"),settingsIcon=document.createElement("ha-icon"),filters=document.createElement("ha-form"),fab=document.createElement("ha-button"),fabIcon=document.createElement("ha-icon");
      wrapper.className="task-table";
      wrapper.setAttribute("main-page","");
      wrapper.setAttribute("clickable","");
      wrapper.setAttribute("has-fab","");
      wrapper.setAttribute("has-filters","");
      settings.slot="toolbar-icon";
      settings.label=t("settings.title");
      settings.setAttribute("aria-label",t("settings.title"));
      settingsIcon.setAttribute("icon","mdi:cog-outline");
      settings.append(settingsIcon);
      settings.addEventListener("click",event=>{event.stopPropagation();this.settings();});
      filters.className="filters";
      filters.slot="filter-pane";
      filters.addEventListener("value-changed",event=>{event.stopPropagation();this.tableFilters=event.detail?.value||{};this.updateTaskTable();});
      fab.slot="fab";
      fab.setAttribute("size","l");
      fab.textContent=t("common.add_task");
      fabIcon.slot="start";
      fabIcon.setAttribute("icon","mdi:plus");
      fab.prepend(fabIcon);
      fab.addEventListener("click",()=>this.taskEditor(null));
      wrapper.append(settings,filters,fab);
      this.shadowRoot.querySelector(".app").append(wrapper);
      wrapper.addEventListener("row-click",event=>{const task=this.tasks.find(item=>item.id===event.detail?.id);if(task)this.taskViewer(task);});
      wrapper.addEventListener("clear-filter",()=>{this.tableFilters={};this.updateTaskTable();});
    }
    this.updateTaskTable();
  }
  updateTaskTable(){
    const wrapper=this.shadowRoot.querySelector("hass-tabs-subpage-data-table");
    if(!wrapper)return;
    const settings=wrapper.querySelector('[slot="toolbar-icon"]'),filters=wrapper.querySelector('ha-form[slot="filter-pane"]'),fab=wrapper.querySelector('[slot="fab"]'),rows=this.tableRows();
    if(settings){settings.label=t("settings.title");settings.title=t("settings.title");settings.setAttribute("aria-label",t("settings.title"));}
    if(fab){for(const node of [...fab.childNodes])if(node.nodeType===3)node.remove();fab.append(document.createTextNode(t("common.add_task")));}
    if(filters){filters.hass=this._hass;filters.data=this.tableFilters||{};filters.schema=this.filterSchema(rows);filters.computeLabel=schema=>this.filterLabel(schema);}
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
