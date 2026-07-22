import { t } from "./localize.js";

export const NO_DUE_TIMESTAMP = Number.MAX_SAFE_INTEGER;
export const INITIAL_TASK_SORTING = {column:"due_ts",direction:"asc"};
export const TASK_GROUP_COLUMNS = ["recurrence","group","assignee","nfc_tag"];

export function dueTimestamp(value) {
  const match=/^(\d{4})-(\d{2})-(\d{2})$/.exec(String(value||""));
  if(!match)return NO_DUE_TIMESTAMP;
  const year=Number(match[1]),month=Number(match[2]),day=Number(match[3]),date=new Date(year,month-1,day);
  return date.getFullYear()===year&&date.getMonth()===month-1&&date.getDate()===day?date.getTime():NO_DUE_TIMESTAMP;
}

export function sortTaskRows(rows,locale="en") {
  return [...rows].sort((a,b)=>a.due_ts-b.due_ts||(a.name||"").localeCompare(b.name||"",locale));
}

export function taskTableRows(tasks,{groups=[],users=[],tags=[],translate=t,locale="en"}={}) {
  const groupNames=new Map(groups.map(group=>[group.id,group.name]));
  const userNames=new Map(users.map(user=>[user.id,user.name]));
  const tagNames=new Map(tags.map(tag=>[tag.id,tag.name]));
  return sortTaskRows(tasks.map(task=>{
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
    };
  }),locale);
}

export function filterTaskRows(rows,search,locale="en") {
  const needle=String(search||"").trim().toLocaleLowerCase(locale);
  if(!needle)return [...rows];
  return rows.filter(row=>[row.name,row.recurrence,row.group,row.assignee,row.nfc_tag]
    .some(value=>String(value||"").toLocaleLowerCase(locale).includes(needle)));
}

function textCell(value,title) {
  const cell=document.createElement("span");
  cell.textContent=value;
  if(title)cell.title=title;
  return cell;
}

export const withTaskList = Base => class extends Base {
  tagName(task){const id=task?.nfc_tag_id;return id?(this.tags?.find(tag=>tag.id===id)?.name||id):"";}
  due(t){return Boolean(this.today&&t.due_date&&t.due_date<=this.today);}
  dueState(t){return !this.today||!t.due_date||t.due_date>this.today?"ok":t.due_date===this.today?"today":"overdue";}
  tableRows(){return taskTableRows(this.tasks,{groups:this.groups,users:this.users,tags:this.tags,translate:t,locale:this.locale()});}
  filteredTableRows(){return filterTaskRows(this.tableRows(),this.tableSearch,this.locale());}
  tableColumns(){
    const groupable={sortable:true,filterable:false,groupable:true};
    return {
      name:{title:t("table.task"),main:true,sortable:true,filterable:false,flex:3},
      due_ts:{title:t("task.due"),sortable:true,filterable:false,template:row=>textCell(row.task.due_date?this.relativeDate(row.task.due_date):"–",row.task.due_date?this.date(row.task.due_date):"")},
      recurrence:{title:t("table.recurrence"),...groupable},
      group:{title:t("task.group"),...groupable},
      assignee:{title:t("table.assignee"),...groupable},
      nfc_tag:{title:t("task.nfc_tag_id"),...groupable},
      actions:{title:"",label:t("task.actions"),type:"overflow-menu",moveable:false,hideable:false,showNarrow:true,template:row=>this.taskActionButton(row.task)},
    };
  }
  taskActionButton(task){
    const button=document.createElement("ha-icon-button"),icon=document.createElement("ha-icon"),stop=event=>event.stopPropagation();
    button.className="row-action-toggle";
    button.label=t("task.actions");
    button.title=t("task.actions");
    button.setAttribute("aria-label",t("task.actions"));
    button.setAttribute("aria-haspopup","menu");
    button.setAttribute("aria-expanded","false");
    icon.setAttribute("icon","mdi:dots-vertical");
    button.append(icon);
    button.addEventListener("pointerdown",stop);
    button.addEventListener("click",event=>{
      event.preventDefault();
      event.stopPropagation();
      this.showTaskActionMenu(button,task);
    });
    return button;
  }
  render(){
    this.closeActionMenu();
    if(this.tableSearch===undefined)this.tableSearch="";
    if(!this.shadowRoot.querySelector(".app")){
      this.shadowRoot.innerHTML=`<style>:host{display:block;height:100%;background:var(--primary-background-color);color:var(--primary-text-color)}.app,hass-tabs-subpage-data-table{display:block;height:100%}</style><div class="app"></div>`;
      const wrapper=document.createElement("hass-tabs-subpage-data-table"),settings=document.createElement("ha-icon-button"),settingsIcon=document.createElement("ha-icon"),fab=document.createElement("ha-button"),fabIcon=document.createElement("ha-icon");
      wrapper.className="task-table";
      wrapper.setAttribute("main-page","");
      wrapper.setAttribute("clickable","");
      wrapper.setAttribute("has-fab","");
      settings.slot="toolbar-icon";
      settings.label=t("settings.title");
      settings.setAttribute("aria-label",t("settings.title"));
      settingsIcon.setAttribute("icon","mdi:cog-outline");
      settings.append(settingsIcon);
      settings.addEventListener("click",event=>{event.stopPropagation();this.settings();});
      fab.slot="fab";
      fab.setAttribute("variant","brand");
      fab.textContent=t("common.add_task");
      fabIcon.slot="start";
      fabIcon.setAttribute("icon","mdi:plus");
      fab.prepend(fabIcon);
      fab.addEventListener("click",()=>this.taskEditor(null));
      wrapper.append(settings,fab);
      const menu=document.createElement("ha-menu"),edit=document.createElement("ha-md-menu-item"),remove=document.createElement("ha-md-menu-item");
      menu.className="task-action-menu";
      menu.setAttribute("positioning","fixed");
      edit.className="edit";
      remove.className="delete";
      edit.innerHTML=`<ha-icon slot="start" icon="mdi:pencil"></ha-icon><div slot="headline">${t("menu.edit")}</div>`;
      remove.innerHTML=`<ha-icon slot="start" icon="mdi:delete"></ha-icon><div slot="headline">${t("menu.delete")}</div>`;
      menu.append(edit,remove);
      menu.addEventListener("pointerdown",event=>event.stopPropagation());
      menu.addEventListener("click",event=>event.stopPropagation());
      edit.addEventListener("click",event=>{event.stopPropagation();const task=this.menuTask;menu.close?.();if(task)this.taskEditor(task.group_id,task);});
      remove.addEventListener("click",event=>{event.stopPropagation();const task=this.menuTask;menu.close?.();if(task)this.deleteTask(task);});
      this.shadowRoot.querySelector(".app").append(wrapper,menu);
      wrapper.addEventListener("row-click",event=>{const task=this.tasks.find(item=>item.id===event.detail?.id);if(task)this.taskViewer(task);});
      wrapper.addEventListener("value-changed",event=>{this.tableSearch=event.detail?.value||"";this.updateTaskTable();});
      wrapper.addEventListener("grouping-changed",event=>{this.tableGrouping=event.detail?.value||"";});
    }
    this.updateTaskTable();
  }
  showTaskActionMenu(button,task){
    const menu=this.shadowRoot.querySelector(".task-action-menu");
    if(!menu)return;
    if(menu.open&&menu.anchorElement===button){menu.close?.();return;}
    this.menuTask=task;
    menu.anchorElement=button;
    menu.show?.();
  }
  updateTaskTable(){
    const wrapper=this.shadowRoot.querySelector("hass-tabs-subpage-data-table");
    if(!wrapper)return;
    const settings=wrapper.querySelector('[slot="toolbar-icon"]'),fab=wrapper.querySelector('[slot="fab"]'),menu=this.shadowRoot.querySelector(".task-action-menu");
    if(settings){settings.label=t("settings.title");settings.title=t("settings.title");settings.setAttribute("aria-label",t("settings.title"));}
    if(fab){for(const node of [...fab.childNodes])if(node.nodeType===3)node.remove();fab.append(document.createTextNode(t("common.add_task")));}
    if(menu){menu.querySelector(".edit [slot=headline]").textContent=t("menu.edit");menu.querySelector(".delete [slot=headline]").textContent=t("menu.delete");}
    wrapper.hass=this._hass;
    wrapper.route=this.route;
    wrapper.tabs=[{name:"Home Tasker",path:""}];
    wrapper.narrow=Boolean(this.narrow);
    wrapper.isWide=Boolean(this.isWide);
    wrapper.columns=this.tableColumns();
    wrapper.data=this.filteredTableRows();
    wrapper.noDataText=t("table.empty");
    wrapper.searchLabel=t("table.search");
    wrapper.initialSorting=INITIAL_TASK_SORTING;
    wrapper.filter="";
    this.syncNativeTableFilter(wrapper);
  }
  syncNativeTableFilter(wrapper){
    const sync=()=>{
      const root=wrapper.shadowRoot,search=root?.querySelector("ha-input-search"),table=root?.querySelector("ha-data-table");
      if(search&&search.value!==this.tableSearch)search.value=this.tableSearch;
      if(table&&table.filter)table.filter="";
      if(table&&this.tableGrouping!==undefined&&"groupColumn" in table)table.groupColumn=this.tableGrouping||undefined;
    };
    sync();
    if(wrapper.updateComplete?.then)wrapper.updateComplete.then(sync);
    else if(globalThis.customElements?.whenDefined)customElements.whenDefined("hass-tabs-subpage-data-table").then(sync);
  }
};
