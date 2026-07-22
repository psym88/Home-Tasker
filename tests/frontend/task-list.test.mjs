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
const {INITIAL_TASK_SORTING,NO_DUE_TIMESTAMP,TASK_FILTER_COLUMNS,TASK_GROUP_COLUMNS,dueTimestamp,filterTaskTableRows,taskTableRows}=await import("../../custom_components/home_tasker/frontend/task-list.js");

const source=readFileSync(new URL("../../custom_components/home_tasker/frontend/task-list.js",import.meta.url),"utf8");

test("task rows flatten every grouping dimension and resolve ids to names",()=>{
  const tasks=[{id:"laundry",name:"Laundry",due_date:"2026-07-24",frequency:"weekly",group_id:"house",assignee_user_id:"alex",nfc_tag_id:"washer"}];
  const original=structuredClone(tasks);
  const attachments=[{id:"a",task_id:"laundry"},{id:"b",task_id:"laundry"},{id:"c",task_id:"other"}];
  const [row]=taskTableRows(tasks,{groups:[{id:"house",name:"House"}],users:[{id:"alex",name:"Alex"}],tags:[{id:"washer",name:"Washer"}],attachments,translate:key=>key});
  assert.deepEqual({id:row.id,name:row.name,recurrence:row.recurrence,group:row.group,assignee:row.assignee,nfc_tag:row.nfc_tag,files:row.files},{id:"laundry",name:"Laundry",recurrence:"task.weekly",group:"House",assignee:"Alex",nfc_tag:"Washer",files:2});
  assert.equal(row.task,tasks[0]);
  assert.deepEqual(tasks,original);
});

test("missing assignments receive localized searchable group values",()=>{
  const [row]=taskTableRows([{id:"task",name:"Task",frequency:"daily"}],{translate:key=>`translated:${key}`});
  assert.equal(row.group,"translated:task.no_group");
  assert.equal(row.assignee,"translated:task.unassigned");
  assert.equal(row.nfc_tag,"translated:task.no_nfc_tag");
  assert.equal(row.files,0);
});

test("due timestamps validate calendar dates and represent missing dates as the maximum",()=>{
  assert.equal(dueTimestamp("2026-07-22"),new Date(2026,6,22).getTime());
  assert.equal(dueTimestamp("2026-02-30"),NO_DUE_TIMESTAMP);
  assert.equal(dueTimestamp(""),NO_DUE_TIMESTAMP);
});

test("native pane filters combine dimensions and allow multiple values within one dimension",()=>{
  const rows=[
    {id:"1",group:"House",assignee:"Alex",recurrence:"Weekly"},
    {id:"2",group:"Garden",assignee:"Alex",recurrence:"Monthly"},
    {id:"3",group:"House",assignee:"Sam",recurrence:"Daily"},
  ];
  assert.deepEqual(filterTaskTableRows(rows,{group:["House"],assignee:["Alex"]}).map(row=>row.id),["1"]);
  assert.deepEqual(filterTaskTableRows(rows,{recurrence:["Weekly","Daily"]}).map(row=>row.id),["1","3"]);
  assert.equal(filterTaskTableRows(rows,{}).length,3);
});

test("panel uses the native Home Assistant data-table wrapper",()=>{
  assert.match(source,/createElement\("hass-tabs-subpage-data-table"\)/);
  assert.match(source,/wrapper\.data=filterTaskTableRows\(rows,this\.tableFilters\)/);
  assert.match(source,/wrapper\.initialSorting=INITIAL_TASK_SORTING/);
  assert.deepEqual(INITIAL_TASK_SORTING,{column:"due_ts",direction:"asc"});
  assert.doesNotMatch(source,/groupRow\(|wireGroup\(|placeholder-add|class="group"/);
});

test("only the requested dimensions can group the native table",()=>{
  assert.deepEqual(TASK_GROUP_COLUMNS,["recurrence","group","assignee"]);
  for(const column of TASK_GROUP_COLUMNS)assert.match(source,new RegExp(`${column}:\\{title:[^}]+\\.\\.\\.groupable`));
  assert.match(source,/nfc_tag:\{title:[^}]+sortable:true,filterable:true\}/);
  assert.doesNotMatch(source,/initialGroupColumn/);
  assert.doesNotMatch(source,/tableGrouping|table\.groupColumn=/);
});

test("native filter pane exposes group assignee and recurrence filters",()=>{
  assert.deepEqual(TASK_FILTER_COLUMNS,["group","assignee","recurrence"]);
  assert.match(source,/createElement\("ha-form"\)/);
  assert.match(source,/filters\.slot="filter-pane"/);
  assert.match(source,/wrapper\.setAttribute\("has-filters",""\)/);
  assert.match(source,/wrapper\.filters=this\.activeFilterCount\(\)/);
  assert.match(source,/wrapper\.data=filterTaskTableRows\(rows,this\.tableFilters\)/);
  assert.match(source,/wrapper\.addEventListener\("clear-filter"/);
});

test("search is delegated completely to the native Home Assistant table",()=>{
  assert.match(source,/name:\{title:[^}]+filterable:true/);
  assert.match(source,/const groupable=\{sortable:true,filterable:true,groupable:true\}/);
  for(const column of TASK_GROUP_COLUMNS)assert.match(source,new RegExp(`${column}:\\{title:[^}]+\\.\\.\\.groupable`));
  assert.doesNotMatch(source,/tableSearch|filterTaskRows|search-changed|syncNativeTableFilter/);
  assert.doesNotMatch(source,/wrapper\.addEventListener\("value-changed"/);
});

test("panel keeps native settings and add-task controls",()=>{
  assert.match(source,/settings\.slot="toolbar-icon"/);
  assert.match(source,/this\.settings\(\)/);
  assert.match(source,/fab\.slot="fab"/);
  assert.match(source,/fab\.setAttribute\("size","l"\)/);
  assert.doesNotMatch(source,/fab\.setAttribute\("variant","brand"\)/);
  assert.match(source,/this\.taskEditor\(null\)/);
});

test("files column shows the sortable attachment count",()=>{
  assert.match(source,/files:\{title:t\("task\.files"\),sortable:true,filterable:false\}/);
  assert.match(source,/attachments:this\.attachments/);
});

test("task action menu stops pointer and click propagation",()=>{
  assert.match(source,/createElement\("ha-dropdown"\)/);
  assert.match(source,/createElement\("ha-dropdown-item"\)/);
  assert.match(source,/dropdown\.addEventListener\("pointerdown",stop\)/);
  assert.match(source,/dropdown\.addEventListener\("click",stop\)/);
  assert.match(source,/dropdown\.addEventListener\("wa-select"/);
  assert.match(source,/if\(action==="edit"\)this\.taskEditor\(task\.group_id,task\)/);
  assert.match(source,/if\(action==="delete"\)this\.deleteTask\(task\)/);
});

test("row clicks continue to open the existing task viewer",()=>{
  assert.match(source,/row-click[\s\S]*this\.taskViewer\(task\)/);
});
