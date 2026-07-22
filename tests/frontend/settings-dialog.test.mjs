import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

test("settings uses a native dialog with a collapsible import/export section", () => {
  const source = readFileSync(new URL("../../custom_components/home_tasker/frontend/native-settings-dialog.js", import.meta.url), "utf8");
  assert.match(source, /show-dialog/);
  assert.match(source, /<ha-adaptive-dialog/);
  assert.match(source, /<ha-expansion-panel outlined>/);
  assert.match(source, /slot="header"/);
  assert.doesNotMatch(source, /<details>|<summary>|summary::after/);
  assert.match(source, /application\/zip/);
  assert.match(source, /confirmAction/);
});

test("panel archive import relies on its Home Tasker event after the request", () => {
  const source = readFileSync(new URL("../../custom_components/home_tasker/frontend/main.js", import.meta.url), "utf8");
  assert.match(source, /fetch\("\/api\/home_tasker\/archive"/);
  assert.match(source, /method:"POST"/);
  const importMethod = source.match(/async importArchive\(file\)\{[^\n]+/)?.[0] || "";
  assert.doesNotMatch(importMethod, /this\.load\(\)/);
  assert.match(source, /connection\.subscribeEvents\(\(\)=>this\.load\(\),"home_tasker_event"/);
});
