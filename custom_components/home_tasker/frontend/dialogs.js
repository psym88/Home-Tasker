import { L, esc } from "./shared.js";
import { showFormDialog, showNativeConfirmation } from "./native-form-dialog.js";

const MEDIUM_LABEL_FIELDS=new Set(["name","description","manufacturer","model"]);

export const withDialogs = Base => class extends Base {
  confirmAction(title,message,confirmLabel,tone="danger"){return showNativeConfirmation(this,{title,message,confirmLabel,tone});}
  dialog(title,fields,onSave,after,onCancel){showFormDialog(this,{title,fields,onSave,after,onCancel});}
  field(f){const [key,label,value,required,type="text",opts=[]]=f,labelClass=MEDIUM_LABEL_FIELDS.has(key)?"ht-label-medium":"ht-label-normal",requiredAttribute=required?" required":"",caption=`<span class="${labelClass}">${label}${required?'<span class="required">*</span>':""}</span>`;if(type==="textarea")return `<label data-field="${key}">${caption}<textarea class="ht-content" name="${key}" style="resize:vertical"${requiredAttribute}>${esc(value)}</textarea></label>`;if(type==="select")return `<label data-field="${key}">${caption}<select class="ht-content" name="${key}"${requiredAttribute}>${opts.map(o=>`<option value="${esc(o[0])}" ${value===o[0]?"selected":""}>${esc(o[1])}</option>`).join("")}</select></label>`;if(type==="labels")return `<label data-field="${key}">${caption}<input name="${key}" type="hidden" value="${esc(JSON.stringify(value||[]))}"><ha-selector></ha-selector></label>`;return `<label data-field="${key}">${caption}<input class="ht-content" name="${key}" type="${type}" value="${esc(value)}"${requiredAttribute} ${type==="number"?'min="1"':""}></label>`;}
};
