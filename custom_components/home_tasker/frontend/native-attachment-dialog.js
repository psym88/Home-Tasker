import { esc } from "./shared.js";

export const ATTACHMENT_DIALOG_TAG="home-tasker-attachment-dialog";

export function showAttachmentDialog(dispatcher,file,url){dispatcher.dispatchEvent(new CustomEvent("show-dialog",{bubbles:true,composed:true,detail:{dialogTag:ATTACHMENT_DIALOG_TAG,dialogImport:()=>customElements.whenDefined(ATTACHMENT_DIALOG_TAG),dialogParams:{file,url},addHistory:true}}));}

export function attachmentPreviewHtml(file,url){const type=String(file.content_type||"").toLowerCase(),safeUrl=esc(url),name=esc(file.filename||"Datei");if(type.startsWith("image/"))return `<img src="${safeUrl}" alt="${name}">`;if(type.startsWith("video/"))return `<video src="${safeUrl}" controls></video>`;if(type.startsWith("audio/"))return `<audio src="${safeUrl}" controls></audio>`;return `<iframe src="${safeUrl}" title="${name}"></iframe>`;}

export class HomeTaskerAttachmentDialog extends HTMLElement {
  constructor(){super();this.attachShadow({mode:"open"});this.open=false;}
  showDialog({file,url}){this.file=file;this.url=url;this.open=true;this.render();}
  closeDialog(){if(!this.open)return true;this.open=false;const dialog=this.shadowRoot.querySelector("ha-adaptive-dialog");if(dialog)dialog.open=false;return true;}
  dialogClosed(){this.open=false;this.file=null;this.url=null;this.shadowRoot.innerHTML="";this.dispatchEvent(new CustomEvent("dialog-closed",{bubbles:true,composed:true,detail:{dialog:this.localName}}));}
  render(){this.shadowRoot.innerHTML=`<style>:host{color:var(--primary-text-color)}ha-adaptive-dialog{--dialog-content-padding:0}.preview{display:flex;align-items:center;justify-content:center;box-sizing:border-box;min-height:240px;height:min(72vh,760px);padding:0;background:var(--primary-background-color);overflow:hidden}.preview img,.preview video{display:block;max-width:100%;max-height:100%;object-fit:contain}.preview audio{width:min(560px,calc(100% - 32px))}.preview iframe{display:block;width:100%;height:100%;border:0;background:white}ha-dialog-footer{padding:0 24px max(16px,var(--safe-area-inset-bottom))}</style><ha-adaptive-dialog width="large" flexcontent><ha-icon-button slot="headerNavigationIcon" class="close" label="Schließen"><ha-icon icon="mdi:close"></ha-icon></ha-icon-button><span slot="headerTitle">${esc(this.file.filename||"Datei")}</span><div class="preview">${attachmentPreviewHtml(this.file,this.url)}</div><ha-dialog-footer slot="footer"><ha-button class="download" slot="primaryAction" variant="brand"><ha-icon icon="mdi:download"></ha-icon> Herunterladen</ha-button></ha-dialog-footer></ha-adaptive-dialog>`;const dialog=this.shadowRoot.querySelector("ha-adaptive-dialog");dialog.open=true;dialog.addEventListener("closed",()=>this.dialogClosed(),{once:true});this.shadowRoot.querySelector(".close").onclick=()=>this.closeDialog();this.shadowRoot.querySelector(".download").onclick=()=>{const link=document.createElement("a");link.href=this.url;link.download=this.file.filename||"";link.click();};}
}

if(!customElements.get(ATTACHMENT_DIALOG_TAG))customElements.define(ATTACHMENT_DIALOG_TAG,HomeTaskerAttachmentDialog);
