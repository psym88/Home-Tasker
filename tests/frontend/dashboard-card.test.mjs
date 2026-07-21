import assert from "node:assert/strict";
import test from "node:test";

globalThis.HTMLElement = class {};
globalThis.customElements = {definitions:new Map(),get(name){return this.definitions.get(name);},define(name,value){this.definitions.set(name,value);}};
globalThis.window = {};
globalThis.CustomEvent = class {constructor(type,options){this.type=type;Object.assign(this,options);}};

const {DEFAULT_CARD_CONFIG,HomeTaskerCardEditor,UNASSIGNED,canEditCard,dashboardCardBodyHtml,dashboardTaskRowHtml,dueStatus,filterDashboardTasks,normalizeCardConfig,sortDashboardTasks}=await import("../../custom_components/home_tasker/frontend/dashboard-card.js");
const {HomeTaskerBase,HomeTaskerPanel}=await import("../../custom_components/home_tasker/frontend/main.js");
const {EDITOR_FILE_GRID}=await import("../../custom_components/home_tasker/frontend/task-editor.js");
const {TASK_DIALOG_TAG,showTaskDialog}=await import("../../custom_components/home_tasker/frontend/native-task-dialog.js");
const {CONFIRM_DIALOG_TAG,FORM_DIALOG_TAG,formDialogFooterHtml,formDialogLayoutStyles,showFormDialog,showNativeConfirmation}=await import("../../custom_components/home_tasker/frontend/native-form-dialog.js");
const {ROW_ACTION_MENU_STYLES,actionMenuEventIsInside}=await import("../../custom_components/home_tasker/frontend/action-menu.js");

const tasks=[
  {id:"old",name:"Wischen",due_date:"2026-07-20",group_id:"house",assignee_user_id:"alice"},
  {id:"today",name:"Abwasch",due_date:"2026-07-21",group_id:"kitchen",assignee_user_id:null},
  {id:"soon",name:"Bad",due_date:"2026-07-24",group_id:"house",assignee_user_id:"bob"},
  {id:"later",name:"Fenster",due_date:"2026-08-01",group_id:"house",assignee_user_id:null},
];

test("default config shows overdue and today",()=>assert.deepEqual(filterDashboardTasks(tasks,DEFAULT_CARD_CONFIG,"2026-07-21").map(task=>task.id),["old","today"]));
test("due day window includes its future boundary",()=>assert.deepEqual(filterDashboardTasks(tasks,{due_days:3},"2026-07-21").map(task=>task.id),["old","today","soon"]));
test("null due day window includes every due date",()=>assert.equal(filterDashboardTasks(tasks,{due_days:null},"2026-07-21").length,4));
test("group and assignee filters use OR within and AND between",()=>assert.deepEqual(filterDashboardTasks(tasks,{due_days:null,group_ids:["house","garage"],assignee_user_ids:["alice",UNASSIGNED]},"2026-07-21").map(task=>task.id),["old","later"]));

test("sorting supports both directions and an ascending name tiebreaker without mutation",()=>{const input=[{id:"b",name:"Zulu",due_date:"2026-07-21"},{id:"a",name:"Alpha",due_date:"2026-07-21"},{id:"c",name:"Später",due_date:"2026-07-22"}],original=[...input];assert.deepEqual(sortDashboardTasks(input,"asc").map(task=>task.id),["a","b","c"]);assert.deepEqual(sortDashboardTasks(input,"desc").map(task=>task.id),["c","a","b"]);assert.deepEqual(input,original);});
test("normalization preserves null and sanitizes invalid values",()=>{assert.equal(normalizeCardConfig({due_days:null}).due_days,null);assert.equal(normalizeCardConfig({due_days:-2,mode:"other"}).due_days,0);assert.equal(normalizeCardConfig({mode:"other"}).mode,"view");});

test("due status separates overdue, today, and future dates",()=>{assert.equal(dueStatus("2026-07-20","2026-07-21"),"overdue");assert.equal(dueStatus("2026-07-21","2026-07-21"),"today");assert.equal(dueStatus("2026-07-22","2026-07-21"),"future");});
test("view rows omit action controls and assignment metadata",()=>{const html=dashboardTaskRowHtml(tasks[0],false,"gestern","overdue");assert.doesNotMatch(html,/dots-vertical|row-action-toggle|alice|house/);assert.match(html,/Wischen/);assert.match(html,/due-label overdue/);});
test("edit rows contain a gray accessible vertical-dots action control",()=>{const html=dashboardTaskRowHtml(tasks[0],true,"gestern","overdue");assert.match(html,/class="row-action-toggle icon"/);assert.match(html,/aria-haspopup="menu"/);assert.match(html,/color:var\(--secondary-text-color\)/);assert.match(html,/mdi:dots-vertical/);});
test("row action menu has neutral edit and red delete hover treatments",()=>{assert.match(ROW_ACTION_MENU_STYLES,/button:hover[^}]+ha-color-fill-neutral-quiet-hover/);assert.match(ROW_ACTION_MENU_STYLES,/button\.danger:hover[^}]+ha-color-fill-alert-quiet-hover/);assert.match(ROW_ACTION_MENU_STYLES,/error-color/);});
test("shadow-DOM retargeting does not close the menu before an action click",()=>{const host={},menu={contains:()=>false},anchor={};assert.equal(actionMenuEventIsInside({target:host,composedPath:()=>[{},menu,host]},menu,anchor),true);assert.equal(actionMenuEventIsInside({target:host,composedPath:()=>[{},host]},menu,anchor),false);});
test("edit mode falls back to view for non-admin users",()=>{assert.equal(canEditCard({mode:"edit"},{user:{is_admin:false}}),false);assert.equal(canEditCard({mode:"edit"},{user:{is_admin:true}}),true);});

test("editor update emits a dashboard-local config change",()=>{const editor=Object.create(HomeTaskerCardEditor.prototype);editor.config={...DEFAULT_CARD_CONFIG};editor.render=()=>{};let event;editor.dispatchEvent=value=>{event=value;};editor.update({mode:"edit",group_ids:["house"]});assert.equal(event.type,"config-changed");assert.equal(event.detail.config.mode,"edit");assert.deepEqual(event.detail.config.group_ids,["house"]);});
test("repeated hass updates do not rerender and steal editor focus",()=>{const editor=Object.create(HomeTaskerCardEditor.prototype);editor.loaded=true;let renders=0;editor.render=()=>{renders++;};Object.getOwnPropertyDescriptor(HomeTaskerCardEditor.prototype,"hass").set.call(editor,{user:{is_admin:true}});assert.equal(renders,0);});
test("panel uses an unregistered shared base instead of becoming the card base",async()=>{const {HomeTaskerCard}=await import("../../custom_components/home_tasker/frontend/dashboard-card.js");assert.equal(Object.getPrototypeOf(HomeTaskerPanel),HomeTaskerBase);assert.equal(Object.getPrototypeOf(HomeTaskerCard),HomeTaskerBase);assert.notEqual(Object.getPrototypeOf(HomeTaskerCard),HomeTaskerPanel);});
test("task viewer opens through Home Assistant's native show-dialog contract",()=>{let event;const controller={dispatchEvent:value=>{event=value;}};showTaskDialog(controller,tasks[0]);assert.equal(event.type,"show-dialog");assert.equal(event.bubbles,true);assert.equal(event.composed,true);assert.equal(event.detail.dialogTag,TASK_DIALOG_TAG);assert.equal(event.detail.dialogParams.task,tasks[0]);});
test("editors and confirmations use registered native dialog contracts",()=>{const events=[],controller={dispatchEvent:event=>events.push(event)};showFormDialog(controller,{title:"Editor",fields:[]});showNativeConfirmation(controller,{title:"Delete",message:"Sure?",confirmLabel:"Delete"});assert.equal(events[0].detail.dialogTag,FORM_DIALOG_TAG);assert.equal(events[1].detail.dialogTag,CONFIRM_DIALOG_TAG);assert.ok(events.every(event=>event.bubbles&&event.composed));});
test("native form dialogs include collapsible layout and chevron styles",()=>{const css="<style>.details-content{display:none}.details.open>.details-toggle ha-icon{transform:rotate(90deg)}</style>";assert.equal(formDialogLayoutStyles({dialogLayoutStyles:()=>css}),css);});
test("native editor actions use the same adaptive-dialog footer as the viewer",()=>{const html=formDialogFooterHtml();assert.match(html,/ha-dialog-footer slot="footer"/);assert.match(html,/ha-button class="save" slot="primaryAction" variant="brand"/);assert.doesNotMatch(html,/<button/);});
test("viewer and editor attachment rows keep short extensions adjacent and truncate long names",()=>{const controller=Object.create(HomeTaskerBase.prototype);controller.signedFiles=new Map();const html=controller.fileLink({id:"file",filename:"short.pdf"});assert.match(html,/class="filename-base"[^>]+flex:0 1 auto[^>]*>short</);assert.match(html,/class="filename-extension"[^>]*>\.pdf</);assert.match(html,/max-width:100%/);assert.equal(EDITOR_FILE_GRID,"display:grid;grid-template-columns:minmax(0,1fr) max-content 44px;gap:8px;align-items:center");});
test("task and group editor popups no longer expose delete actions",()=>{assert.equal(typeof HomeTaskerBase.prototype.mountTaskActions,"undefined");assert.equal(typeof HomeTaskerBase.prototype.mountGroupActions,"undefined");});
test("dashboard add action renders before task elements",()=>{const html=dashboardCardBodyHtml('<div class="task-row"></div>',true);assert.ok(html.indexOf("card-actions")<html.indexOf("task-row"));});
test("row menu deletion keeps confirmation and reloads after the mutation",async()=>{const controller=Object.create(HomeTaskerBase.prototype),messages=[];controller.confirmAction=async()=>true;controller.ws=async message=>messages.push(message);let loads=0;controller.load=async()=>{loads++;};await controller.deleteTask({id:"task",name:"Task"});assert.deepEqual(messages,[{type:"home_tasker/task/delete",task_id:"task"}]);assert.equal(loads,1);});
