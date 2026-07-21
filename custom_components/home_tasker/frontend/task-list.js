import { L, esc } from "./shared.js";
import { ROW_ACTION_MENU_STYLES, rowActionButtonHtml } from "./action-menu.js";

export const TASK_ROW_BACKGROUND = "transparent";
export const TASK_ROW_HOVER_BACKGROUND = "rgba(var(--rgb-primary-text-color),0.04)";
export const LIST_SECONDARY_ACTION_COLOR = "var(--secondary-text-color)";

export function sortTasksByDue(tasks, locale="de") {
  return [...tasks].sort((a,b)=>(a.due_date||"").localeCompare(b.due_date||"")||(a.name||"").localeCompare(b.name||"",locale));
}

export const withTaskList = Base => class extends Base {
  tasksOf(id){ return this.tasks.filter(t=>t.group_id===id); }
  sortedTasks(tasks){if(this.sort==="due")return sortTasksByDue(tasks);return [...tasks].sort((a,b)=>a.name.localeCompare(b.name,"de"));}
  due(t){return Boolean(this.today&&t.due_date<=this.today);}
  sorted(){ const g=[...this.groups]; if(this.sort==="due"){const first=x=>this.tasksOf(x.id).reduce((date,t)=>t.due_date<date?t.due_date:date,"9999-12-31");g.sort((a,b)=>first(a).localeCompare(first(b))||a.name.localeCompare(b.name,"de"));}else g.sort((a,b)=>a.name.localeCompare(b.name,"de")); return g; }
  render(){
    this.closeActionMenu();
    if(!this.shadowRoot.querySelector(".app")) this.shadowRoot.innerHTML=`${this.styles()}<style>.task:hover{background:${TASK_ROW_HOVER_BACKGROUND}}.task{background:${TASK_ROW_BACKGROUND};cursor:grab;user-select:none}.task.dragging{opacity:.45}.group-head.drop-target{outline:2px solid var(--primary-color);outline-offset:-2px;background:var(--secondary-background-color)}</style><div class="app"></div>`;
    const app=this.shadowRoot.querySelector(".app");
    app.innerHTML=`<style>main{padding-bottom:96px}.task{cursor:pointer;user-select:auto}.floating-add{position:fixed;right:16px;bottom:calc(16px + env(safe-area-inset-bottom));z-index:5;padding:11px 16px;background:var(--primary-color);color:#fff;border-radius:12px;box-shadow:var(--ha-card-box-shadow,0 3px 8px #0004);font:inherit}.version{right:10px;left:auto;top:8px;bottom:auto}</style><main><header><div><h1>Home Tasker</h1><p>Wiederkehrende Aufgaben im Blick behalten</p></div></header>
      <nav><i></i><button class="link expand" style="color:${LIST_SECONDARY_ACTION_COLOR}">${this.groups.every(g=>this.expanded.has(g.id))?"Alle zuklappen":"Alle aufklappen"}</button><select class="sort"><option value="name">Name</option><option value="due">Fälligkeit</option></select></nav>
      <section>${this.sorted().map(g=>this.groupRow(g)).join("")}</section><button class="floating-add">${L.addTask}</button><small class="version">v${this.constructor.version}</small></main>`;
    app.insertAdjacentHTML("beforeend",ROW_ACTION_MENU_STYLES+this.themeStyles()+this.buttonThemeStyles()+this.iconHoverStyles()+this.groupListStyles());
    app.querySelector(".sort").value=this.sort;
    app.querySelector(".expand").onclick=()=>{ const all=this.groups.every(g=>this.expanded.has(g.id)); this.expanded=all?new Set():new Set(this.groups.map(g=>g.id)); this.render(); };
    app.querySelector(".sort").onchange=e=>{this.sort=e.target.value;this.render();};
    app.querySelector(".floating-add").onclick=()=>this.taskEditor(null);
    app.querySelectorAll(".group").forEach(el=>this.wireGroup(el));
  }
  groupRow(g){ const shown=this.sortedTasks(this.tasksOf(g.id)), open=this.expanded.has(g.id), due=shown.filter(t=>this.due(t)).length;
    return `<article class="group" data-group="${g.id}"><div class="group-head" role="button" tabindex="0"><ha-icon class="chevron" icon="mdi:chevron-${open?"down":"right"}"></ha-icon><strong>${esc(g.name)}</strong>${due?`<span class="pill open-count">${due}</span>`:""}<i></i>${rowActionButtonHtml("group",g.id)}</div>${open?`<div class="tasks">${shown.map(t=>this.taskRow(t)).join("")}</div>`:""}</article>`; }
  fileNameParts(filename){const name=String(filename||""),dot=name.lastIndexOf(".");return dot>0&&dot<name.length-1?{base:name.slice(0,dot),extension:name.slice(dot)}:{base:name,extension:""};}
  filePill(file){const name=String(file.filename||""),parts=this.fileNameParts(name),url=this.signedFiles.get(file.id),content=`<span style="min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${esc(parts.base)}</span><span style="flex:none;white-space:nowrap">${esc(parts.extension)}</span>`,style="display:inline-flex;align-items:center;max-width:160px;min-width:0;color:var(--primary-color);text-decoration:none";return url?`<a class="pill file-pill" href="${esc(url)}" target="_blank" rel="noopener noreferrer" title="${esc(name)}" style="${style}">${content}</a>`:`<span class="pill file-pill" title="${esc(name)}" style="${style}">${content}</span>`;}
  taskRow(t){ const files=this.attachments.filter(a=>a.task_id===t.id),assignee=this.users.find(user=>user.id===t.assignee_user_id),filePills=files.map(file=>this.filePill(file)).join("");return `<div class="task" data-task="${t.id}" tabindex="0" style="display:grid;grid-template-columns:minmax(0,1fr) 44px;align-items:center;gap:4px;padding:5px 6px 7px 10px"><div class="task-body" style="display:block;min-width:0"><strong>${esc(t.name)}</strong><div class="pills" style="display:flex;gap:6px;flex-wrap:wrap;align-items:center"><span class="pill due-date ${this.due(t)?"due":"ok"}" title="${esc(this.date(t.due_date))}">${esc(this.relativeDate(t.due_date))}</span>${assignee?`<span class="pill">${esc(assignee.name)}</span>`:""}</div>${filePills?`<div class="pills" style="display:flex;gap:6px;flex-wrap:wrap;align-items:center;margin-top:6px">${filePills}</div>`:""}</div>${rowActionButtonHtml("task",t.id)}</div>`; }
  wireGroup(el){ const g=this.groups.find(x=>x.id===el.dataset.group),head=el.querySelector(".group-head"),toggle=()=>{this.expanded.has(g.id)?this.expanded.delete(g.id):this.expanded.add(g.id);this.render();};head.onclick=toggle;head.onkeydown=e=>{if(e.key==="Enter"||e.key===" ")toggle();};const groupActions=el.querySelector('.row-action-toggle[data-action-kind="group"]');groupActions.onclick=e=>{e.stopPropagation();this.actionMenu(groupActions,()=>this.groupEditor(g),()=>this.deleteGroup(g));};el.querySelectorAll("[data-task]").forEach(row=>{const t=this.tasks.find(x=>x.id===row.dataset.task),taskActions=row.querySelector('.row-action-toggle[data-action-kind="task"]');row.onclick=()=>this.taskViewer(t);row.onkeydown=e=>{if(e.target===row&&(e.key==="Enter"||e.key===" "))this.taskViewer(t);};row.querySelectorAll(".file-pill").forEach(file=>file.onclick=e=>e.stopPropagation());taskActions.onclick=e=>{e.stopPropagation();this.actionMenu(taskActions,()=>this.taskEditor(g.id,t),()=>this.deleteTask(t));};}); }
};
