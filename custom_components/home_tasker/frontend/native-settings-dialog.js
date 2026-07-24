import { esc } from "./shared.js";
import { errorMessage, t } from "./localize.js";

export const SETTINGS_DIALOG_TAG="home-tasker-settings-dialog";

export function showSettingsDialog(controller){controller.dispatchEvent(new CustomEvent("show-dialog",{bubbles:true,composed:true,detail:{dialogTag:SETTINGS_DIALOG_TAG,dialogImport:()=>customElements.whenDefined(SETTINGS_DIALOG_TAG),dialogParams:{controller},addHistory:true}}));}

export class HomeTaskerSettingsDialog extends HTMLElement {
  constructor(){super();this.attachShadow({mode:"open"});this.open=false;}
  showDialog({controller}){this.controller=controller;this.open=true;this.render();}
  closeDialog(){if(!this.open)return true;this.open=false;const dialog=this.shadowRoot.querySelector("ha-adaptive-dialog");if(dialog)dialog.open=false;return true;}
  dialogClosed(){this.open=false;this.controller=null;this.shadowRoot.innerHTML="";this.dispatchEvent(new CustomEvent("dialog-closed",{bubbles:true,composed:true,detail:{dialog:this.localName}}));}
  status(message,error=false){const status=this.shadowRoot.querySelector(".status");status.textContent=message;status.classList.toggle("error",error);}
  async exportArchive(){this.status(t("settings.exporting"));try{await this.controller.exportArchive();this.status(t("settings.export_complete"));}catch(err){this.status(t("common.error",{message:errorMessage(err)}),true);}}
  chooseImport(){this.shadowRoot.querySelector("input[type=file]").click();}
  async importArchive(file){if(!file)return;const confirmed=await this.controller.confirmAction(t("settings.import_confirm_title"),t("settings.import_confirm"),t("settings.import"),"danger");if(!confirmed)return;this.status(t("settings.importing"));try{await this.controller.importArchive(file);this.status(t("settings.import_complete"));}catch(err){this.status(t("common.error",{message:errorMessage(err)}),true);}}
  render(){this.shadowRoot.innerHTML=`${this.controller.typographyStyles()}<style>:host{color:var(--primary-text-color)}ha-adaptive-dialog{--dialog-content-padding:0}ha-expansion-panel{--input-fill-color:transparent}.content{padding:16px 24px 24px;overflow:auto}.details-content{display:flex;flex-direction:column;gap:12px;padding:0 16px 16px}.hint{margin:0;color:var(--secondary-text-color)}.status{min-height:20px}.status.error{color:var(--error-color)}input{display:none}</style><ha-adaptive-dialog width="medium" flexcontent><ha-icon-button slot="headerNavigationIcon" class="close" label="${esc(t("common.close"))}"><ha-icon icon="mdi:close"></ha-icon></ha-icon-button><span slot="headerTitle">${esc(t("settings.title"))}</span><div class="content"><ha-expansion-panel outlined><span slot="header" class="ht-label-medium">${esc(t("settings.import_export"))}</span><div class="details-content"><p class="hint ht-content">${esc(t("settings.archive_hint"))}</p><div class="status ht-content" role="status"></div><ha-dialog-footer><ha-button class="export" slot="secondaryAction" variant="brand"><ha-icon icon="mdi:archive-arrow-down-outline"></ha-icon> ${esc(t("settings.export"))}</ha-button><ha-button class="import" slot="primaryAction" variant="danger"><ha-icon icon="mdi:archive-arrow-up-outline"></ha-icon> ${esc(t("settings.import"))}</ha-button></ha-dialog-footer><input type="file" accept=".zip,application/zip"></div></ha-expansion-panel></div></ha-adaptive-dialog>`;const dialog=this.shadowRoot.querySelector("ha-adaptive-dialog"),input=this.shadowRoot.querySelector("input");dialog.open=true;dialog.addEventListener("closed",()=>this.dialogClosed(),{once:true});this.shadowRoot.querySelector(".close").onclick=()=>this.closeDialog();this.shadowRoot.querySelector(".export").onclick=()=>this.exportArchive();this.shadowRoot.querySelector(".import").onclick=()=>this.chooseImport();input.onchange=()=>{const file=input.files?.[0];input.value="";this.importArchive(file);};}
}

if(!customElements.get(SETTINGS_DIALOG_TAG))customElements.define(SETTINGS_DIALOG_TAG,HomeTaskerSettingsDialog);
