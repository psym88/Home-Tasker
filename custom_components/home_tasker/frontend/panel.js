// Home Tasker panel — custom element core.
// The UI is split across topic modules (list/viewer/editor/format) whose
// methods are mixed onto the prototype below via Object.assign. They use
// `this` exactly as class methods do, so no data plumbing is required.
import { STYLE_LINK } from "./utils.js";
import * as format from "./format.js";
import * as list from "./list.js";
import * as viewer from "./viewer.js";
import * as editor from "./editor.js";

class HomeTaskerPanel extends HTMLElement {
  constructor(){ super(); this.attachShadow({mode:"open"}); this.groups=[]; this.tasks=[]; this.attachments=[]; this.users=[]; this.today=""; this.signedFiles=new Map(); this.expanded=new Set(); this.sort="name"; this.loading=false; this.refreshTimer=null; this.detailsObserver=new MutationObserver(()=>this.prepareDetails());this.detailsObserver.observe(this.shadowRoot,{childList:true,subtree:true}); }
  connectedCallback(){if(!this.refreshTimer)this.refreshTimer=setInterval(()=>{if(document.visibilityState==="visible")this.load();},30000);}
  disconnectedCallback(){clearInterval(this.refreshTimer);this.refreshTimer=null;}
  set hass(value){ this._hass=value; if(!this.loaded){ this.loaded=true; this.load(); } }
  async ws(msg){ return this._hass.connection.sendMessagePromise(msg); }
  async load(){if(!this._hass||this.loading)return;this.loading=true;try{const d=await this.ws({type:"home_tasker/list"});this.groups=d.groups||[];this.tasks=d.tasks||[];this.attachments=d.attachments||[];this.users=d.users||[];this.today=d.today||"";this.signedFiles=new Map(Object.entries(d.signed_files||{}));this.render();}catch(err){if(!this.shadowRoot.querySelector(".app"))this.shadowRoot.innerHTML=`${STYLE_LINK}<div class="app"><main><h1>Home Tasker</h1><p>Die Daten konnten nicht geladen werden. Ein neuer Versuch folgt automatisch.</p></main></div><div class="dialogs"></div>`;console.error("Home Tasker load failed",err);}finally{this.loading=false;}}
  async signFiles(){const result=await this.ws({type:"home_tasker/attachment/sign_all"});this.signedFiles=new Map(Object.entries(result.urls||{}));}
  tasksOf(id){ return this.tasks.filter(t=>t.group_id===id); }
  sortedTasks(tasks){const sorted=[...tasks];if(this.sort==="due")sorted.sort((a,b)=>a.due_date.localeCompare(b.due_date)||a.name.localeCompare(b.name,"de"));else sorted.sort((a,b)=>a.name.localeCompare(b.name,"de"));return sorted;}
  due(t){return Boolean(this.today&&t.due_date<=this.today);}
  sorted(){ const g=[...this.groups]; if(this.sort==="due"){const first=x=>this.tasksOf(x.id).reduce((date,t)=>t.due_date<date?t.due_date:date,"9999-12-31");g.sort((a,b)=>first(a).localeCompare(first(b))||a.name.localeCompare(b.name,"de"));}else g.sort((a,b)=>a.name.localeCompare(b.name,"de")); return g; }
  modalHeader(title,id){return `<div class="modal-header"><button type="button" class="modal-close" aria-label="Schließen" title="Schließen"><ha-icon icon="mdi:close"></ha-icon></button><h2${id?` id="${id}"`:""}>${title}</h2></div>`;}
  token(){return this._hass?.auth?.data?.access_token||null;}
  async upload(taskId,files,onUploaded){for(const file of files){const fd=new FormData();fd.append("task_id",taskId);fd.append("file",file,file.name);const r=await fetch("/api/home_tasker/upload",{method:"POST",headers:this.token()?{authorization:`Bearer ${this.token()}`}:{},body:fd});if(!r.ok)throw new Error(`Upload fehlgeschlagen (${r.status})`);const record=await r.json();this.attachments.push(record);if(onUploaded)onUploaded(record);}await this.signFiles();}
}
Object.assign(HomeTaskerPanel.prototype, format, list, viewer, editor);
if(!customElements.get("home-tasker-panel"))customElements.define("home-tasker-panel",HomeTaskerPanel);
