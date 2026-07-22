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
const { LIST_SECONDARY_ACTION_COLOR, TASK_ROW_BACKGROUND, TASK_ROW_HOVER_BACKGROUND, sortTasksByDue, withTaskList } = await import("../../custom_components/home_tasker/frontend/task-list.js");

test("task rows remain transparent", () => {
  assert.equal(TASK_ROW_BACKGROUND, "transparent");
  assert.equal(TASK_ROW_HOVER_BACKGROUND, "rgba(var(--rgb-primary-text-color),0.04)");
});

test("list rows use vertical-dots action menus", () => {
  class TaskListModel extends withTaskList(class {}) {}
  const model = new TaskListModel();
  model.groups = [];
  model.tasks = [];
  model.attachments = [];
  model.users = [];
  model.expanded = new Set();
  model.sort = "name";
  model.due = () => false;
  model.date = value => value;
  model.relativeDate = value => value;
  model.locale = () => "en";

  assert.equal(LIST_SECONDARY_ACTION_COLOR, "var(--secondary-text-color)");
  assert.match(model.groupRow({ id: "group", name: "Group" }), /data-action-kind="group"[\s\S]*?mdi:dots-vertical/);
  assert.match(model.taskRow({ id: "task", name: "Task", due_date: "2026-07-21" }), /data-action-kind="task"[\s\S]*?mdi:dots-vertical/);
});

test("sortTasksByDue sorts by due date and then by name", () => {
  const tasks = [
    { id: "3", name: "Mopping", due_date: "2026-07-23" },
    { id: "2", name: "Laundry", due_date: "2026-07-22" },
    { id: "1", name: "Dishes", due_date: "2026-07-22" },
  ];

  assert.deepEqual(sortTasksByDue(tasks).map(task => task.id), ["1", "2", "3"]);
});

test("sortTasksByDue handles an empty list", () => {
  assert.deepEqual(sortTasksByDue([]), []);
});

test("sortTasksByDue does not mutate its input", () => {
  const tasks = [
    { id: "2", name: "Later", due_date: "2026-07-24" },
    { id: "1", name: "Earlier", due_date: "2026-07-21" },
  ];
  const original = [...tasks];

  sortTasksByDue(tasks);

  assert.deepEqual(tasks, original);
});

test("grouped task rows preserve panel sorting and due badges", () => {
  class TaskListModel extends withTaskList(class {}) {}
  const model = new TaskListModel();
  model.tasks = [
    { id: "later", group_id: "chores", name: "Mopping", due_date: "2026-07-23" },
    { id: "due", group_id: "chores", name: "Dishes", due_date: "2026-07-21" },
  ];
  model.attachments = [];
  model.users = [];
  model.signedFiles = new Map();
  model.expanded = new Set(["chores"]);
  model.sort = "due";
  model.today = "2026-07-21";
  model.date = value => value;
  model.relativeDate = value => value;
  model.locale = () => "en";

  const html = model.groupRow({ id: "chores", name: "Household" });

  assert.ok(html.includes('<span class="pill open-count">1</span>'));
  assert.ok(html.indexOf('data-task="due"') < html.indexOf('data-task="later"'));
});

test("task-list titles use the primary theme color", () => {
  class TaskListModel extends withTaskList(class {}) {}
  const model = new TaskListModel();
  model.attachments = [];
  model.users = [];
  model.due = () => false;
  model.date = value => value;
  model.relativeDate = value => value;
  model.locale = () => "en";
  assert.match(model.taskRow({ id: "task", name: "Task", due_date: "2026-07-21" }), /<strong class="ht-content">Task<\/strong>/);
  const source = readFileSync(new URL("../../custom_components/home_tasker/frontend/task-list.js", import.meta.url), "utf8");
  assert.match(source, /\.task-body>strong\{color:var\(--primary-color\)!important\}/);
});

test("task-list titles show the assigned Home Assistant tag name as a small pill", () => {
  class TaskListModel extends withTaskList(class {}) {}
  const model = new TaskListModel();
  model.attachments = [];
  model.users = [{ id: "alex", name: "Alex" }];
  model.tags = [{ id: "tag-1", name: "Washing machine" }];
  model.due = () => false;
  model.date = value => value;
  model.relativeDate = value => value;
  const html = model.taskRow({ id: "task", name: "Laundry", assignee_user_id: "alex", nfc_tag_id: "tag-1", due_date: "2026-07-21" });
  assert.ok(html.indexOf("Laundry") < html.indexOf("Alex"));
  assert.ok(html.indexOf("Alex") < html.indexOf("Washing machine"));
  assert.match(html, /mdi:account/);
  assert.match(html, /class="pill ht-content-small"><ha-icon icon="mdi:nfc"><\/ha-icon>Washing machine<\/span>/);
});

test("expanded groups end with a group-bound add-task placeholder", () => {
  class TaskListModel extends withTaskList(class {}) {}
  const model = new TaskListModel();
  model.tasks = [{ id: "task", group_id: "chores", name: "Task", due_date: "2026-07-21" }];
  model.attachments = [];
  model.users = [];
  model.signedFiles = new Map();
  model.expanded = new Set(["chores"]);
  model.sort = "name";
  model.today = "2026-07-21";
  model.date = value => value;
  model.relativeDate = value => value;
  model.locale = () => "en";

  const html = model.groupRow({ id: "chores", name: "Household" });
  assert.ok(html.indexOf('data-task="task"') < html.indexOf('class="placeholder-add group-add"'));
  assert.match(html, /mdi:plus[\s\S]*Add task/);
  model.expanded.clear();
  assert.doesNotMatch(model.groupRow({ id: "chores", name: "Household" }), /group-add/);
});

test("task list replaces the floating action with top and group placeholders", () => {
  const source = readFileSync(new URL("../../custom_components/home_tasker/frontend/task-list.js", import.meta.url), "utf8");
  assert.doesNotMatch(source, /floating-add|position:fixed/);
  assert.match(source, /class="placeholder-add list-add"/);
  assert.match(source, /groupAdd\.onclick=\(\)=>this\.taskEditor\(g\.id\)/);
  assert.match(source, /border:1px dashed var\(--divider-color\)/);
  assert.match(source, /\.placeholder-add\{justify-content:center;text-align:center\}/);
});

test("task list exposes settings above the list", () => {
  const source = readFileSync(new URL("../../custom_components/home_tasker/frontend/task-list.js", import.meta.url), "utf8");
  assert.match(source, /class="settings"[\s\S]*mdi:cog-outline[\s\S]*settings\.title/);
  assert.match(source, /querySelector\("\.settings"\)\.onclick=\(\)=>this\.settings\(\)/);
});

test("task-list attachment pills open in-app instead of a new browser page", () => {
  class TaskListModel extends withTaskList(class {}) {}
  const model = new TaskListModel();
  model.signedFiles = new Map([["file", "/signed/file"]]);
  const html = model.filePill({ id: "file", filename: "manual.pdf" });
  assert.match(html, /class="pill file-pill file-open" data-file-open="file"/);
  assert.match(html, /mdi:paperclip/);
  assert.doesNotMatch(html, /target="_blank"|<a /);
});

test("task-list sorting uses the planning-style themed select", () => {
  const source = readFileSync(new URL("../../custom_components/home_tasker/frontend/task-list.js", import.meta.url), "utf8");
  assert.match(source, /<select class="sort" aria-label="\$\{t\("panel\.sort"\)\}">/);
  assert.match(source, /\.sort\{[^}]*padding:9px[^}]*border:1px solid var\(--divider-color\)[^}]*background:var\(--primary-background-color\)[^}]*color:var\(--primary-text-color\)[^}]*font:inherit/);
  assert.match(source, /\.sort"\)\.onchange/);
  assert.doesNotMatch(source, /<ha-select class="sort"/);
});

test("task-list due pills distinguish today from overdue", async () => {
  const { DUE_DATE_STYLES } = await import("../../custom_components/home_tasker/frontend/task-list.js");
  class TaskListModel extends withTaskList(class {}) {}
  const model = new TaskListModel();
  model.today = "2026-07-21";
  model.attachments = [];
  model.users = [];
  model.tags = [];
  model.signedFiles = new Map();
  model.date = value => value;
  model.relativeDate = value => value;
  assert.match(model.taskRow({ id: "today", name: "Today", due_date: "2026-07-21" }), /due-date today/);
  assert.match(model.taskRow({ id: "old", name: "Old", due_date: "2026-07-20" }), /due-date overdue/);
  assert.match(DUE_DATE_STYLES, /\.due-date\.today\{color:var\(--warning-color/);
  assert.match(DUE_DATE_STYLES, /\.due-date\.overdue\{color:var\(--error-color/);
  assert.doesNotMatch(DUE_DATE_STYLES, /font-weight/);
});
