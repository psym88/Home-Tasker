import assert from "node:assert/strict";
import test from "node:test";

const { GROUP_HEADER_BACKGROUND, GROUP_HEADER_HOVER_BACKGROUND, withStyles } = await import("../../custom_components/home_tasker/frontend/styles.js");

test("group headers use neutral Home Assistant resting and hover fills", () => {
  assert.equal(GROUP_HEADER_BACKGROUND, "var(--ha-color-fill-neutral-quiet-resting,var(--secondary-background-color))");
  assert.equal(GROUP_HEADER_HOVER_BACKGROUND, "var(--ha-color-fill-neutral-quiet-hover,var(--secondary-background-color))");
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
