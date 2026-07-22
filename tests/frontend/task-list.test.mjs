import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

globalThis.HTMLElement = class {};
globalThis.customElements = { get: () => undefined, define: () => undefined };
globalThis.fetch = async url => {
  const language = String(url).match(/\/([a-z]{2,3})\.json$/)?.[1] || "en";
  const catalog = JSON.parse(readFileSync(new URL(`../../custom_components/home_tasker/translations/${language}.json`, import.meta.url), "utf8"));
  return { ok: true, json: async () => catalog };
};

const {ready,setLanguage}=await import("../../custom_components/home_tasker/frontend/localize.js");
await ready;
await setLanguage("en");
const {INITIAL_TASK_SORTING,NO_DUE_TIMESTAMP,TASK_GROUP_COLUMNS,dueTimestamp,filterTaskRows,sortTaskRows,taskTableRows}=await import("../../custom_components/home_tasker/frontend/task-list.js");

const source=readFileSync(new URL("../../custom_components/home_tasker/frontend/task-list.js",import.meta.url),"utf8");

test("task rows flatten every grouping dimension and resolve ids to names",()=>{
  const tasks=[{id:"laundry",name:"Laundry",due_date:"2026-07-24",frequency:"weekly",group_id:"house",assignee_user_id:"alex",nfc_tag_id:"washer"}];
  const original=structuredClone(tasks);
  const [row]=taskTableRows(tasks,{groups:[{id:"house",name:"House"}],users:[{id:"alex",name:"Alex"}],tags:[{id:"washer",name:"Washer"}],translate:key=>key,locale:"en"});
  assert.deepEqual({id:row.id,name:row.name,recurrence:row.recurrence,group:row.group,assignee:row.assignee,nfc_tag:row.nfc_tag},{id:"laundry",name:"Laundry",recurrence:"task.weekly",group:"House",assignee:"Alex",nfc_tag:"Washer"});
  assert.equal(row.task,tasks[0]);
  assert.deepEqual(tasks,original);
});

test("missing assignments receive localized searchable group values",()=>{
  const [row]=taskTableRows([{id:"task",name:"Task",frequency:"daily"}],{translate:key=>`translated:${key}`});
  assert.equal(row.group,"translated:task.no_group");
  assert.equal(row.assignee,"translated:task.unassigned");
  assert.equal(row.nfc_tag,"translated:task.no_nfc_tag");
});

test("due timestamps validate calendar dates and put missing dates last",()=>{
  assert.equal(dueTimestamp("2026-07-22"),new Date(2026,6,22).getTime());
  assert.equal(dueTimestamp("2026-02-30"),NO_DUE_TIMESTAMP);
  assert.equal(dueTimestamp(""),NO_DUE_TIMESTAMP);
  const rows=sortTaskRows([{id:"none",name:"None",due_ts:NO_DUE_TIMESTAMP},{id:"z",name:"Zulu",due_ts:1},{id:"a",name:"Alpha",due_ts:1}]);
  assert.deepEqual(rows.map(row=>row.id),["a","z","none"]);
});

test("search filters the supplied data across all visible values",()=>{
  const rows=[
    {id:"1",name:"Laundry",recurrence:"Weekly",group:"House",assignee:"Alex",nfc_tag:"Washer"},
    {id:"2",name:"Dishes",recurrence:"Daily",group:"Kitchen",assignee:"Sam",nfc_tag:"Sink"},
  ];
  for(const query of ["laundry","weekly","house","alex","washer"]){
    assert.deepEqual(filterTaskRows(rows,query).map(row=>row.id),["1"]);
  }
  assert.equal(filterTaskRows(rows,"").length,2);
  assert.equal(filterTaskRows(rows,"missing").length,0);
});

test("panel uses the native Home Assistant data-table wrapper",()=>{
  assert.match(source,/createElement\("hass-tabs-subpage-data-table"\)/);
  assert.match(source,/wrapper\.data=this\.filteredTableRows\(\)/);
  assert.match(source,/wrapper\.initialSorting=INITIAL_TASK_SORTING/);
  assert.deepEqual(INITIAL_TASK_SORTING,{column:"due_ts",direction:"asc"});
  assert.doesNotMatch(source,/groupRow\(|wireGroup\(|placeholder-add|class="group"/);
});

test("only the requested dimensions can group the native table",()=>{
  assert.deepEqual(TASK_GROUP_COLUMNS,["recurrence","group","assignee","nfc_tag"]);
  for(const column of TASK_GROUP_COLUMNS)assert.match(source,new RegExp(`${column}:\\{title:[^}]+\\.\\.\\.groupable`));
  assert.doesNotMatch(source,/initialGroupColumn/);
  assert.match(source,/table\.groupColumn=this\.tableGrouping\|\|undefined/);
});

test("search reduces data while the internal table filter stays empty",()=>{
  assert.match(source,/value-changed[\s\S]*tableSearch[\s\S]*updateTaskTable/);
  assert.match(source,/wrapper\.filter=""/);
  assert.match(source,/if\(table&&table\.filter\)table\.filter=""/);
});

test("panel keeps native settings and add-task controls",()=>{
  assert.match(source,/settings\.slot="toolbar-icon"/);
  assert.match(source,/this\.settings\(\)/);
  assert.match(source,/fab\.slot="fab"/);
  assert.match(source,/this\.taskEditor\(null\)/);
});

test("task action menu stops pointer and click propagation",()=>{
  assert.match(source,/addEventListener\("pointerdown",stop\)/);
  assert.match(source,/event\.preventDefault\(\);\s*event\.stopPropagation\(\);/);
  assert.match(source,/createElement\("ha-menu"\)/);
  assert.match(source,/createElement\("ha-md-menu-item"\)/);
  assert.match(source,/menu\.addEventListener\("click",event=>event\.stopPropagation\(\)\)/);
  assert.match(source,/this\.showTaskActionMenu\(button,task\)/);
});

test("row clicks continue to open the existing task viewer",()=>{
  assert.match(source,/row-click[\s\S]*this\.taskViewer\(task\)/);
});
