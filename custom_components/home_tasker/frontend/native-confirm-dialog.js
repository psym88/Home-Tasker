import { esc } from "./shared.js";
import { t } from "./localize.js";

export const CONFIRM_DIALOG_TAG="home-tasker-confirm-dialog";

export function showNativeConfirmation(controller,{title,message,confirmLabel,tone="danger"}){return new Promise(resolve=>controller.dispatchEvent(new CustomEvent("show-dialog",{bubbles:true,composed:true,detail:{dialogTag:CONFIRM_DIALOG_TAG,dialogImport:()=>customElements.whenDefined(CONFIRM_DIALOG_TAG),dialogParams:{title,message,confirmLabel,tone,resolve}}})));}

export const withConfirmation = Base => class extends Base {
  confirmAction(title,message,confirmLabel,tone="danger"){return showNativeConfirmation(this,{title,message,confirmLabel,tone});}
};

export class HomeTaskerConfirmDialog extends HTMLElement {
  constructor(){super();this.attachShadow({mode:"open"});this.open=false;this.resolved=false;}
  showDialog(params){Object.assign(this,params);this.open=true;this.resolved=false;this.render();}
  finish(value){if(this.resolved)return;this.resolved=true;this.resolve(value);this.closeDialog();}
  closeDialog(){if(!this.open)return true;if(!this.resolved){this.resolved=true;this.resolve(false);}this.open=false;const dialog=this.shadowRoot.querySelector("ha-adaptive-dialog");if(dialog)dialog.open=false;return true;}
  dialogClosed(){if(!this.resolved){this.resolved=true;this.resolve(false);}this.open=false;this.dispatchEvent(new CustomEvent("dialog-closed",{bubbles:true,composed:true,detail:{dialog:this.localName}}));this.shadowRoot.innerHTML="";}
  render(){this.shadowRoot.innerHTML=`<style>ha-adaptive-dialog{--dialog-content-padding:0}.message{padding:16px 24px 24px;color:var(--primary-text-color);line-height:var(--ha-line-height-normal,1.4)}ha-dialog-footer{padding:0 24px max(16px,var(--safe-area-inset-bottom))}</style><ha-adaptive-dialog width="small"><span slot="headerTitle">${esc(this.title)}</span><div class="message">${esc(this.message)}</div><ha-dialog-footer slot="footer"><ha-button class="cancel" slot="secondaryAction" appearance="plain">${t("common.cancel")}</ha-button><ha-button class="confirm" slot="primaryAction" variant="${this.tone==="danger"?"danger":"brand"}">${esc(this.confirmLabel)}</ha-button></ha-dialog-footer></ha-adaptive-dialog>`;const dialog=this.shadowRoot.querySelector("ha-adaptive-dialog");dialog.open=true;dialog.addEventListener("closed",()=>this.dialogClosed(),{once:true});this.shadowRoot.querySelector(".cancel").onclick=()=>this.finish(false);this.shadowRoot.querySelector(".confirm").onclick=()=>this.finish(true);}
}

if(!customElements.get(CONFIRM_DIALOG_TAG))customElements.define(CONFIRM_DIALOG_TAG,HomeTaskerConfirmDialog);
