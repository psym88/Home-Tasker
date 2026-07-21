export const VERSION = "0.2.81";
import { HomeTaskerPanel } from "./main.js";

HomeTaskerPanel.version = VERSION;
if(!customElements.get("home-tasker-panel"))customElements.define("home-tasker-panel",HomeTaskerPanel);
