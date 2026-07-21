import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

globalThis.HTMLElement = class {};
globalThis.customElements = { get: () => undefined, define: () => undefined };

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

  assert.equal(LIST_SECONDARY_ACTION_COLOR, "var(--secondary-text-color)");
  assert.match(model.groupRow({ id: "group", name: "Group" }), /data-action-kind="group"[\s\S]*?mdi:dots-vertical/);
  assert.match(model.taskRow({ id: "task", name: "Task", due_date: "2026-07-21" }), /data-action-kind="task"[\s\S]*?mdi:dots-vertical/);
});

test("sortTasksByDue sorts by due date and then by name", () => {
  const tasks = [
    { id: "3", name: "Wischen", due_date: "2026-07-23" },
    { id: "2", name: "Bad", due_date: "2026-07-22" },
    { id: "1", name: "Abwasch", due_date: "2026-07-22" },
  ];

  assert.deepEqual(sortTasksByDue(tasks).map(task => task.id), ["1", "2", "3"]);
});

test("sortTasksByDue handles an empty list", () => {
  assert.deepEqual(sortTasksByDue([]), []);
});

test("sortTasksByDue does not mutate its input", () => {
  const tasks = [
    { id: "2", name: "Später", due_date: "2026-07-24" },
    { id: "1", name: "Früher", due_date: "2026-07-21" },
  ];
  const original = [...tasks];

  sortTasksByDue(tasks);

  assert.deepEqual(tasks, original);
});

test("grouped task rows preserve panel sorting and due badges", () => {
  class TaskListModel extends withTaskList(class {}) {}
  const model = new TaskListModel();
  model.tasks = [
    { id: "later", group_id: "chores", name: "Wischen", due_date: "2026-07-23" },
    { id: "due", group_id: "chores", name: "Abwasch", due_date: "2026-07-21" },
  ];
  model.attachments = [];
  model.users = [];
  model.signedFiles = new Map();
  model.expanded = new Set(["chores"]);
  model.sort = "due";
  model.today = "2026-07-21";
  model.date = value => value;
  model.relativeDate = value => value;

  const html = model.groupRow({ id: "chores", name: "Haushalt" });

  assert.ok(html.includes('<span class="pill open-count">1</span>'));
  assert.ok(html.indexOf('data-task="due"') < html.indexOf('data-task="later"'));
});

test("task-list titles use the secondary text color", () => {
  class TaskListModel extends withTaskList(class {}) {}
  const model = new TaskListModel();
  model.attachments = [];
  model.users = [];
  model.due = () => false;
  model.date = value => value;
  model.relativeDate = value => value;
  assert.match(model.taskRow({ id: "task", name: "Task", due_date: "2026-07-21" }), /<strong style="color:var\(--secondary-text-color\)">Task<\/strong>/);
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

  const html = model.groupRow({ id: "chores", name: "Haushalt" });
  assert.ok(html.indexOf('data-task="task"') < html.indexOf('class="placeholder-add group-add"'));
  assert.match(html, /mdi:plus[\s\S]*Task hinzufügen/);
  model.expanded.clear();
  assert.doesNotMatch(model.groupRow({ id: "chores", name: "Haushalt" }), /group-add/);
});

test("task list replaces the floating action with top and group placeholders", () => {
  const source = readFileSync(new URL("../../custom_components/home_tasker/frontend/task-list.js", import.meta.url), "utf8");
  assert.doesNotMatch(source, /floating-add|position:fixed/);
  assert.match(source, /class="placeholder-add list-add"/);
  assert.match(source, /groupAdd\.onclick=\(\)=>this\.taskEditor\(g\.id\)/);
  assert.match(source, /border:1px dashed var\(--divider-color\)/);
  assert.match(source, /\.placeholder-add\{justify-content:center;text-align:center\}/);
});

test("task-list attachment pills open in-app instead of a new browser page", () => {
  class TaskListModel extends withTaskList(class {}) {}
  const model = new TaskListModel();
  model.signedFiles = new Map([["file", "/signed/file"]]);
  const html = model.filePill({ id: "file", filename: "manual.pdf" });
  assert.match(html, /class="pill file-pill file-open" data-file-open="file"/);
  assert.doesNotMatch(html, /target="_blank"|<a /);
});

test("task-list sorting uses the planning-style themed select", () => {
  const source = readFileSync(new URL("../../custom_components/home_tasker/frontend/task-list.js", import.meta.url), "utf8");
  assert.match(source, /<select class="sort" aria-label="Sortierung">/);
  assert.match(source, /\.sort\{[^}]*padding:9px[^}]*border:1px solid var\(--divider-color\)[^}]*background:var\(--primary-background-color\)[^}]*color:var\(--primary-text-color\)[^}]*font:inherit/);
  assert.match(source, /\.sort"\)\.onchange/);
  assert.doesNotMatch(source, /<ha-select class="sort"/);
});
