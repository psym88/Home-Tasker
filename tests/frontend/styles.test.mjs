import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const { TYPOGRAPHY_STYLES, withStyles } = await import("../../custom_components/home_tasker/frontend/styles.js");
const source = readFileSync(new URL("../../custom_components/home_tasker/frontend/styles.js", import.meta.url), "utf8");

test("shared styles contain only current shell form typography and pill concerns", () => {
  assert.doesNotMatch(source, /groupListStyles|GROUP_LIST_BACKGROUND|GROUP_HEADER_BACKGROUND|compactDetailsStyles|dialogLayoutStyles|iconHoverStyles|taskSurfaceStyles/);
  assert.doesNotMatch(source, /\.group-head|\.tasks\{|\.chev|\.filter\{|\.version|details-toggle|summary::after/);
});

test("shell styles no longer contain the removed handcrafted task list", () => {
  class StyleModel extends withStyles(class {}) {}
  const css = new StyleModel().styles();
  assert.match(css, /:host\{display:block;min-height:100%/);
  assert.doesNotMatch(css, /\.group\{|\.task\{|\.pill|\.overlay|\.modal/);
});

test("form styles are limited to the remaining form and structural layouts", () => {
  class StyleModel extends withStyles(class {}) {}
  const css = new StyleModel().formStyles();
  assert.match(css, /form,label/);
  assert.match(css, /\.details-content\{display:flex/);
  assert.match(css, /\[data-field="description"\] textarea\{min-height:120px\}/);
  assert.doesNotMatch(css, /\.drop-zone/);
  assert.doesNotMatch(css, /details-toggle|summary|box-shadow|!important/);
});

test("shared typography classes use Home Assistant tokens", () => {
  assert.match(TYPOGRAPHY_STYLES, /\.ht-label-medium\{color:var\(--primary-text-color\);font-size:var\(--ha-font-size-m,14px\);font-weight:var\(--ha-font-weight-medium,500\)\}/);
  assert.match(TYPOGRAPHY_STYLES, /\.ht-content\{color:var\(--secondary-text-color\);font-size:var\(--ha-font-size-m,14px\)/);
  assert.doesNotMatch(TYPOGRAPHY_STYLES, /!important|summary|details/);
});

test("pills retain one small token-based style for custom card metadata", () => {
  class StyleModel extends withStyles(class {}) {}
  const model = new StyleModel();
  assert.match(model.pillIconCss(), /font-size:var\(--ha-font-size-s,12px\)/);
  assert.match(model.pillIconCss(), /\.pill ha-icon\{--mdc-icon-size:14px/);
  assert.equal(model.pillStyles(), `<style>${model.pillIconCss()}</style>`);
});
