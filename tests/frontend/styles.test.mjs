import assert from "node:assert/strict";
import test from "node:test";

const { withStyles } = await import("../../custom_components/home_tasker/frontend/styles.js");

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
