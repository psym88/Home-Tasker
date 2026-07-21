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
