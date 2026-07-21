import assert from "node:assert/strict";
import test from "node:test";

const { withStyles } = await import("../../custom_components/home_tasker/frontend/styles.js");

test("icon hover uses a primary Home Assistant fill distinct from list-row hover", () => {
  class StyleModel extends withStyles(class {}) {}
  const model = new StyleModel();

  assert.match(
    model.iconHoverStyles(),
    /background:var\(--ha-color-fill-primary-quiet-hover,color-mix\(in srgb,var\(--primary-color\) 12%,transparent\)\)/,
  );
  assert.doesNotMatch(
    model.iconHoverStyles(),
    /ha-color-fill-neutral-quiet-hover|secondary-background-color/,
  );
});
