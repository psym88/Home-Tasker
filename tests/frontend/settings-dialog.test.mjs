import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

test("settings uses a native dialog with a collapsible import/export section", () => {
  const source = readFileSync(new URL("../../custom_components/home_tasker/frontend/native-settings-dialog.js", import.meta.url), "utf8");
  assert.match(source, /show-dialog/);
  assert.match(source, /<ha-adaptive-dialog/);
  assert.match(source, /<details><summary/);
  assert.match(source, /application\/zip/);
  assert.match(source, /confirmAction/);
});

test("panel archive calls use authenticated download and destructive import endpoints", () => {
  const source = readFileSync(new URL("../../custom_components/home_tasker/frontend/main.js", import.meta.url), "utf8");
  assert.match(source, /fetch\("\/api\/home_tasker\/archive"/);
  assert.match(source, /method:"POST"/);
  assert.match(source, /await this\.load\(\)/);
});
