import { L, esc } from "./shared.js";
import { t } from "./localize.js";

export const TASK_DIALOG_TAG="home-tasker-task-dialog";
const COMPLETION_DIALOG_TAG="home-tasker-completion-dialog";
const VIEWER_FILE_GRID="display:grid;grid-template-columns:minmax(0,1fr) max-content;gap:8px;align-items:center;min-height:40px";

function detailBox(title,content,className){
  return `<ha-expansion-panel outlined class="${className}"><span slot="header">${esc(title)}</span><div class="details-content">${content}</div></ha-expansion-panel>`;
}

function taskFilesBoxHtml(controller,task){
  const files=controller.attachments.filter(file=>file.task_id===task.task_id),rows=files.length?files.map(file=>`<div data-file="${esc(file.attachment_id)}" class="file-row" style="${VIEWER_FILE_GRID}">${controller.fileLink(file)}<span class="file-size" style="justify-self:end;white-space:nowrap">${controller.size(file.size)}</span></div>`).join(""):`<small class="ht-content">${L.noFiles}</small>`;
  return detailBox(L.files,`<div class="file-list">${rows}</div>`,"files-box");
}

function taskHistoryBoxHtml(controller,entries){
  const rows=Array.isArray(entries)?(entries.length?entries.map(entry=>controller.historyRow(entry)).join(""):`<small class="ht-content">${L.noHistory}</small>`):t("common.loading");
  return detailBox(L.history,`<div class="history-list ht-content">${rows}</div>`,"history-box");
}

function confirmCompletion(dispatcher,task){
  return new Promise(resolve=>dispatcher.dispatchEvent(new CustomEvent("show-dialog",{bubbles:true,composed:true,detail:{dialogTag:COMPLETION_DIALOG_TAG,dialogImport:()=>customElements.whenDefined(COMPLETION_DIALOG_TAG),dialogParams:{task,resolve}}})));
}

class HomeTaskerCompletionDialog extends HTMLElement {
  constructor(){super();this.attachShadow({mode:"open"});this.resolved=false;}
  showDialog({task,resolve}){this.task=task;this.resolve=resolve;this.resolved=false;this.render();}
  finish(value){if(this.resolved)return;this.resolved=true;this.resolve(value);this.closeDialog();}
  closeDialog(){if(!this.resolved){this.resolved=true;this.resolve(false);}const dialog=this.shadowRoot.querySelector("ha-adaptive-dialog");if(dialog)dialog.open=false;return true;}
  dialogClosed(){if(!this.resolved){this.resolved=true;this.resolve(false);}this.dispatchEvent(new CustomEvent("dialog-closed",{bubbles:true,composed:true,detail:{dialog:this.localName}}));this.shadowRoot.innerHTML="";}
  render(){this.shadowRoot.innerHTML=`<style>ha-adaptive-dialog{--dialog-content-padding:0}.message{padding:16px 24px 24px;color:var(--primary-text-color)}ha-dialog-footer{padding:0 24px max(16px,var(--safe-area-inset-bottom))}</style><ha-adaptive-dialog width="small"><span slot="headerTitle">${t("task.complete_title")}</span><div class="message">${esc(t("task.complete_confirm",{name:this.task.task_name}))}</div><ha-dialog-footer slot="footer"><ha-button class="cancel" slot="secondaryAction" appearance="plain">${t("common.cancel")}</ha-button><ha-button class="confirm" slot="primaryAction" variant="brand">${t("task.complete")}</ha-button></ha-dialog-footer></ha-adaptive-dialog>`;const dialog=this.shadowRoot.querySelector("ha-adaptive-dialog");dialog.open=true;dialog.addEventListener("closed",()=>this.dialogClosed(),{once:true});this.shadowRoot.querySelector(".cancel").onclick=()=>this.finish(false);this.shadowRoot.querySelector(".confirm").onclick=()=>this.finish(true);}
}

export function showTaskDialog(controller,task){controller.dispatchEvent(new CustomEvent("show-dialog",{bubbles:true,composed:true,detail:{dialogTag:TASK_DIALOG_TAG,dialogImport:()=>customElements.whenDefined(TASK_DIALOG_TAG),dialogParams:{controller,task},addHistory:true}}));}

export class HomeTaskerTaskDialog extends HTMLElement {
  constructor(){super();this.attachShadow({mode:"open"});this.open=false;}
  showDialog({controller,task}){this.controller=controller;this.task=task;this.open=true;this.render();this.addAssignmentChips();this.loadHistory();}
  closeDialog(){if(!this.open)return true;this.open=false;const dialog=this.shadowRoot.querySelector("ha-adaptive-dialog");if(dialog)dialog.open=false;return true;}
  dialogClosed(){this.open=false;this.controller=null;this.task=null;this.shadowRoot.innerHTML="";this.dispatchEvent(new CustomEvent("dialog-closed",{bubbles:true,composed:true,detail:{dialog:this.localName}}));}
  confirmCompletion(){return confirmCompletion(this,this.task);}
  async complete(){const button=this.shadowRoot.querySelector(".complete"),notes=(this.shadowRoot.querySelector(".completion-notes").value||"").trim()||null;if(!await this.confirmCompletion())return;button.disabled=true;try{await this.controller.ws({type:"home_tasker/task/complete",task_id:this.task.task_id,notes});this.closeDialog();}finally{button.disabled=false;}}
  async loadHistory(){try{const data=await this.controller.ws({type:"home_tasker/history/list",task_id:this.task.task_id});if(!this.open)return;const history=this.shadowRoot.querySelector(".history-list");history.innerHTML=data.history.length?data.history.map(entry=>this.controller.historyRow(entry)).join(""):`<small class="ht-content">${L.noHistory}</small>`;}catch(error){if(this.open)this.shadowRoot.querySelector(".history-list").innerHTML=`<small class="ht-content">${esc(t("history.load_failed",{message:error.message||error}))}</small>`;}}
  addAssignmentChips(){const chips=this.shadowRoot.querySelector("ha-chip-set"),tagName=this.controller.tagName(this.task),fileCount=this.controller.attachments.filter(file=>file.task_id===this.task.task_id).length;if(tagName){const chip=document.createElement("ha-assist-chip");chip.label=tagName;chip.innerHTML='<ha-icon slot="icon" icon="mdi:nfc"></ha-icon>';chips.append(chip);}const files=document.createElement("ha-assist-chip");files.label=String(fileCount);files.innerHTML='<ha-icon slot="icon" icon="mdi:file-outline"></ha-icon>';chips.append(files);for(const name of this.controller.labelNames(this.task)){const chip=document.createElement("ha-assist-chip");chip.label=name;chip.innerHTML='<ha-icon slot="icon" icon="mdi:label-outline"></ha-icon>';chips.append(chip);}}
  render(){const controller=this.controller,task=this.task,assignee=controller.users.find(user=>user.id===task.assignee_id),due=task.task_due?`<ha-assist-chip label="${esc(controller.date(task.task_due))}"><ha-icon slot="icon" icon="mdi:calendar"></ha-icon></ha-assist-chip>`:"",description=task.task_description?`<ha-markdown breaks></ha-markdown>`:`<p class="ht-content">${t("task.no_description")}</p>`,notes=`<textarea class="completion-notes ht-content" style="resize:vertical" aria-label="${esc(t("task.completion_notes"))}" placeholder="${esc(t("task.completion_notes_placeholder"))}"></textarea>`;this.shadowRoot.innerHTML=`${controller.typographyStyles()}${controller.formStyles()}<style>:host{color:var(--primary-text-color)}ha-adaptive-dialog{--dialog-content-padding:0}ha-expansion-panel{--input-fill-color:transparent}.content{display:flex;flex-direction:column;gap:12px;padding:16px 24px 24px;overflow:auto}ha-chip-set{display:flex;gap:8px;flex-wrap:wrap}.recurrence{overflow-wrap:anywhere;margin:0}.details-content{display:flex;flex-direction:column;gap:8px;padding:0 16px 16px}.detail-row{display:flex;align-items:center;gap:8px;padding:7px 0}.detail-row span,.filename{flex:1}.file-size{flex:0;white-space:nowrap}ha-dialog-footer{padding:0 24px max(16px,var(--safe-area-inset-bottom))}</style><ha-adaptive-dialog width="medium" flexcontent><ha-icon-button slot="headerNavigationIcon" class="close" label="${t("common.close")}"><ha-icon icon="mdi:close"></ha-icon></ha-icon-button><span slot="headerTitle">${esc(task.task_name)}</span><div class="content"><ha-chip-set>${due}<ha-assist-chip label="${esc(assignee?.name||t("task.unassigned"))}"><ha-icon slot="icon" icon="mdi:account"></ha-icon></ha-assist-chip></ha-chip-set><p class="recurrence ht-content">${esc(controller.scheduleText(task))}</p>${description}${notes}${taskFilesBoxHtml(controller,task)}${taskHistoryBoxHtml(controller,null)}</div><ha-dialog-footer slot="footer"><ha-button class="complete" slot="primaryAction" variant="brand">${t("task.completed")}</ha-button></ha-dialog-footer></ha-adaptive-dialog>`;const markdown=this.shadowRoot.querySelector("ha-markdown");if(markdown)markdown.content=task.task_description;const dialog=this.shadowRoot.querySelector("ha-adaptive-dialog");dialog.open=true;dialog.addEventListener("closed",()=>this.dialogClosed(),{once:true});this.shadowRoot.querySelector(".close").onclick=()=>this.closeDialog();this.shadowRoot.querySelector(".complete").onclick=()=>this.complete();controller.wireFileOpeners(this.shadowRoot,this);}
}

if(!customElements.get(TASK_DIALOG_TAG))customElements.define(TASK_DIALOG_TAG,HomeTaskerTaskDialog);
if(!customElements.get(COMPLETION_DIALOG_TAG))customElements.define(COMPLETION_DIALOG_TAG,HomeTaskerCompletionDialog);
