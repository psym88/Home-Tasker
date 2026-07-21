import assert from "node:assert/strict";
import test from "node:test";

globalThis.HTMLElement = class {};
globalThis.customElements = {definitions:new Map(),get(name){return this.definitions.get(name);},define(name,value){this.definitions.set(name,value);}};
globalThis.window = {};
globalThis.CustomEvent = class {constructor(type,options){this.type=type;Object.assign(this,options);}};

const {DEFAULT_CARD_CONFIG,HomeTaskerCardEditor,UNASSIGNED,canEditCard,dashboardTaskRowHtml,filterDashboardTasks,normalizeCardConfig,sortDashboardTasks}=await import("../../custom_components/home_tasker/frontend/dashboard-card.js");
const {HomeTaskerBase,HomeTaskerPanel}=await import("../../custom_components/home_tasker/frontend/main.js");

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

test("view rows omit edit controls and assignment metadata",()=>{const html=dashboardTaskRowHtml(tasks[0],false,"gestern");assert.doesNotMatch(html,/pencil|edit-task-row|alice|house/);assert.match(html,/Wischen/);assert.match(html,/gestern/);});
test("edit rows contain the pencil control",()=>assert.match(dashboardTaskRowHtml(tasks[0],true,"gestern"),/edit-task-row/));
test("edit mode falls back to view for non-admin users",()=>{assert.equal(canEditCard({mode:"edit"},{user:{is_admin:false}}),false);assert.equal(canEditCard({mode:"edit"},{user:{is_admin:true}}),true);});

test("editor update emits a dashboard-local config change",()=>{const editor=Object.create(HomeTaskerCardEditor.prototype);editor.config={...DEFAULT_CARD_CONFIG};editor.render=()=>{};let event;editor.dispatchEvent=value=>{event=value;};editor.update({mode:"edit",group_ids:["house"]});assert.equal(event.type,"config-changed");assert.equal(event.detail.config.mode,"edit");assert.deepEqual(event.detail.config.group_ids,["house"]);});
test("panel uses an unregistered shared base instead of becoming the card base",async()=>{const {HomeTaskerCard}=await import("../../custom_components/home_tasker/frontend/dashboard-card.js");assert.equal(Object.getPrototypeOf(HomeTaskerPanel),HomeTaskerBase);assert.equal(Object.getPrototypeOf(HomeTaskerCard),HomeTaskerBase);assert.notEqual(Object.getPrototypeOf(HomeTaskerCard),HomeTaskerPanel);});
