import { t } from "./localize.js";

const KEYS={addTask:"common.add_task",fixed:"task.fixed",sliding:"task.sliding",daily:"task.daily",weekly:"task.weekly",monthly:"task.monthly",yearly:"task.yearly",save:"common.save",files:"task.files",history:"task.history",noFiles:"task.no_files",noHistory:"task.no_history"};
export const L=new Proxy({}, {get:(_,key)=>t(KEYS[key]||String(key))});
export const esc = (v) => String(v ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
