export const VERSION = "0.2.80";
import { HomeTaskerPanel } from "./main.js";

HomeTaskerPanel.version = VERSION;
if(!customElements.get("home-tasker-panel"))customElements.define("home-tasker-panel",HomeTaskerPanel);
