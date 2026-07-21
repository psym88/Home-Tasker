import assert from "node:assert/strict";
import test from "node:test";

globalThis.HTMLElement = class {};
globalThis.customElements = { get: () => undefined, define: () => undefined };

const { TASK_ROW_BACKGROUND, sortTasksByDue, withTaskList } = await import("../../custom_components/home_tasker/frontend/task-list.js");

test("task rows remain transparent", () => {
  assert.equal(TASK_ROW_BACKGROUND, "transparent");
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
