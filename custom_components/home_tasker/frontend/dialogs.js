import { L, esc } from "./shared.js";
import { showFormDialog, showNativeConfirmation } from "./native-form-dialog.js";

export const withDialogs = Base => class extends Base {
  confirmAction(title,message,confirmLabel,tone="danger"){return showNativeConfirmation(this,{title,message,confirmLabel,tone});}
  dialog(title,fields,onSave,after,onCancel){showFormDialog(this,{title,fields,onSave,after,onCancel});}
  closeFormDialog(){return this._activeFormDialog?.closeDialog(true);}
  field(f){const [key,label,value,,type="text",opts=[]]=f,caption=`<span>${label}${key==="name"?'<span class="required">*</span>':""}</span>`;if(type==="textarea")return `<label data-field="${key}">${caption}<textarea name="${key}" style="resize:vertical">${esc(value)}</textarea></label>`;if(type==="select")return `<label data-field="${key}">${caption}<select name="${key}">${opts.map(o=>`<option value="${esc(o[0])}" ${value===o[0]?"selected":""}>${esc(o[1])}</option>`).join("")}</select></label>`;return `<label data-field="${key}">${caption}<input name="${key}" type="${type}" value="${esc(value)}" ${type==="number"?'min="1"':""}></label>`;}
  prepareDetails(root=this.shadowRoot){root.querySelectorAll(".modal .details:not([data-collapsible])").forEach(box=>{const title=box.querySelector(":scope>h3");if(!title)return;box.dataset.collapsible="";const toggle=document.createElement("button"),content=document.createElement("div");toggle.type="button";toggle.className="details-toggle";toggle.setAttribute("aria-expanded","false");toggle.innerHTML=`<h3>${title.innerHTML}</h3><ha-icon icon="mdi:chevron-right"></ha-icon>`;content.className="details-content";[...box.children].forEach(child=>{if(child!==title)content.append(child);});title.replaceWith(toggle);box.append(content);toggle.onclick=()=>{const open=box.classList.toggle("open");toggle.setAttribute("aria-expanded",String(open));};});}
};
