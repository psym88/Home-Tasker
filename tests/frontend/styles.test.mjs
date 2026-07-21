import assert from "node:assert/strict";
import test from "node:test";

const { GROUP_LIST_BACKGROUND, GROUP_HEADER_BACKGROUND, withStyles } = await import("../../custom_components/home_tasker/frontend/styles.js");

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

test("native editors use the requested primary labels and secondary values", () => {
  class StyleModel extends withStyles(class {}) {}
  const css = new StyleModel().editorTypographyStyles();

  assert.match(css, /task-form \[data-field="name"\][^}]+primary-text-color[^}]+ha-font-size-m[^}]+ha-font-weight-medium/);
  assert.match(css, /task-form \[data-field="recurrence_mode"\][^}]+primary-text-color[^}]+ha-font-size-m[^}]+ha-font-weight-normal/);
  assert.match(css, /group-form label>span[^}]+primary-text-color[^}]+ha-font-size-m[^}]+ha-font-weight-medium/);
  assert.match(css, /task-form input[^}]+secondary-text-color[^}]+ha-font-size-m[^}]+ha-font-weight-normal/);
  assert.match(css, /task-form \.history-entry[^}]+secondary-text-color/);
  assert.match(css, /task-form \.details-content small[^}]+secondary-text-color/);
});
