import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const { GROUP_LIST_BACKGROUND, GROUP_HEADER_BACKGROUND, TYPOGRAPHY_STYLES, withStyles } = await import("../../custom_components/home_tasker/frontend/styles.js");

test("group list swaps Home Assistant data-table row and header backgrounds", () => {
  assert.equal(GROUP_LIST_BACKGROUND, "var(--primary-background-color)");
  assert.equal(GROUP_HEADER_BACKGROUND, "var(--data-table-background-color,var(--card-background-color,#fff))");
});

test("icon hover uses the neutral Home Assistant fill", () => {
  class StyleModel extends withStyles(class {}) {}
  const model = new StyleModel();

  assert.match(
    model.iconHoverStyles(),
    /background:var\(--ha-color-fill-neutral-quiet-hover,var\(--secondary-background-color\)\)/,
  );
  assert.doesNotMatch(
    model.iconHoverStyles(),
    /ha-color-fill-primary-quiet-hover|color-mix/,
  );
});

test("all pills use Home Assistant's small font size", () => {
  class StyleModel extends withStyles(class {}) {}
  const model = new StyleModel();

  assert.match(model.themeStyles(), /\.pill\{font-size:var\(--ha-font-size-s\)\}/);
  assert.doesNotMatch(model.styles(), /\.count,\.pill\{[^}]*font-size:/);
});

test("pill icons use one compact shared size", () => {
  class StyleModel extends withStyles(class {}) {}
  const css = new StyleModel().pillIconCss();
  assert.match(css, /\.pill\{display:inline-flex;align-items:center;gap:5px;padding:3px 8px;border-radius:12px;background:var\(--secondary-background-color\);font-size:var\(--ha-font-size-s,12px\);font-weight:var\(--ha-font-weight-normal,400\);line-height:normal\}/);
  assert.match(css, /\.pill ha-icon\{display:block;align-self:center;--mdc-icon-size:14px;width:14px;height:14px;flex:0 0 14px\}/);
});

test("each task-list group has a theme-aware outer border", () => {
  class StyleModel extends withStyles(class {}) {}
  assert.match(new StyleModel().groupListStyles(), /\.group\{[^}]*border:1px solid var\(--divider-color\)/);
});

test("shared dialog layout contains only collapsible content rules", () => {
  class StyleModel extends withStyles(class {}) {}
  const css = new StyleModel().dialogLayoutStyles();
  assert.doesNotMatch(css, /modal-header|modal-close/);
  assert.match(css, /\.details-content\{display:none/);
  assert.match(css, /\.details\.open>\.details-content\{display:flex/);
});

test("panel styles exclude legacy overlays and editor-only layout", () => {
  class StyleModel extends withStyles(class {}) {}
  const model = new StyleModel();
  assert.doesNotMatch(model.styles(), /\.overlay|\.modal\{|form,label|\.actions/);
  assert.match(model.formStyles(), /form,label/);
  assert.match(model.formStyles(), /\.details\{/);
});

test("shared typography classes map to the requested Home Assistant tokens", () => {
  assert.match(TYPOGRAPHY_STYLES, /\.ht-label-medium\{color:var\(--primary-text-color\);font-size:var\(--ha-font-size-m,14px\);font-weight:var\(--ha-font-weight-medium,500\)\}/);
  assert.match(TYPOGRAPHY_STYLES, /\.ht-label-normal\{color:var\(--primary-text-color\);font-size:var\(--ha-font-size-m,14px\);font-weight:var\(--ha-font-weight-normal,400\)\}/);
  assert.match(TYPOGRAPHY_STYLES, /\.ht-content\{color:var\(--secondary-text-color\);font-size:var\(--ha-font-size-m,14px\);font-weight:var\(--ha-font-weight-normal,400\)\}/);
  assert.match(TYPOGRAPHY_STYLES, /\.ht-content-small\{color:var\(--secondary-text-color\);font-size:var\(--ha-font-size-s,12px\);font-weight:var\(--ha-font-weight-normal,400\)\}/);
});

test("legacy field-specific typography overrides are removed", () => {
  const source = readFileSync(new URL("../../custom_components/home_tasker/frontend/styles.js", import.meta.url), "utf8");
  assert.doesNotMatch(source, /editorTypographyStyles|\.task-form \[data-field|\.group-form label/);
  assert.doesNotMatch(TYPOGRAPHY_STYLES, /!important/);
});
