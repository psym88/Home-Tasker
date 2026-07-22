import { L, esc } from "./shared.js";
import { t } from "./localize.js";

export const EDITOR_FILE_GRID="display:grid;grid-template-columns:minmax(0,1fr) max-content 44px;gap:8px;align-items:center";

export function taskFilesBoxHtml(controller,task,{editable=false,pending=new Set()}={}){
  const files=controller.attachments.filter(file=>file.task_id===task.id),rows=files.length?files.map(file=>`<div data-file="${esc(file.id)}" class="detail-row ${pending.has(file.id)?"pending":""}"${editable?` style="${EDITOR_FILE_GRID}"`:""}>${controller.fileLink(file)}<span class="file-size"${editable?' style="justify-self:end;white-space:nowrap"':""}>${controller.size(file.size)}</span>${editable?`<button type="button" class="editor-action remove ${pending.has(file.id)?"":"danger"}" aria-label="${pending.has(file.id)?t("file.undo_remove"):t("file.remove")}" title="${pending.has(file.id)?t("common.undo"):t("common.remove")}" style="justify-self:end"><ha-icon icon="mdi:${pending.has(file.id)?"undo":"delete"}"></ha-icon></button>`:""}</div>`).join(""):`<small class="ht-content">${L.noFiles}</small>`;
  return editable?`<section class="details files-box"><h3 class="ht-label-medium">${L.files}</h3><input type="file" multiple hidden><div class="file-list">${rows}</div><button type="button" class="drop-zone" style="width:100%;min-height:72px;margin-top:10px;border:2px dashed var(--divider-color);background:var(--secondary-background-color);color:var(--secondary-text-color);display:flex;align-items:center;justify-content:center;gap:8px"><ha-icon icon="mdi:tray-arrow-up"></ha-icon><span>${t("file.drop")}</span></button></section>`:`<details class="files-box"><summary class="ht-label-medium">${L.files}</summary><div class="details-content file-list">${rows}</div></details>`;
}

export function taskHistoryBoxHtml(controller,entries,{editable=false,pending=new Set(),status=""}={}){
  const rows=Array.isArray(entries)?(entries.length?entries.map(entry=>controller.historyRow(entry,editable)).join(""):`<small class="ht-content">${L.noHistory}</small>`):(status||t("common.loading"));
  return editable?`<section class="details history-box"><h3 class="ht-label-medium">${L.history}</h3><div class="history-list ht-content">${rows}</div></section>`:`<details class="history-box"><summary class="ht-label-medium">${L.history}</summary><div class="details-content history-list ht-content">${rows}</div></details>`;
}
