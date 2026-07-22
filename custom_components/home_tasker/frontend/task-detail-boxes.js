import { L, esc } from "./shared.js";
import { t } from "./localize.js";

export const EDITOR_FILE_GRID="display:grid;grid-template-columns:minmax(0,1fr) max-content 44px;gap:8px;align-items:center";

export function taskFilesBoxHtml(controller,task,{editable=false,pending=new Set()}={}){
  const files=controller.attachments.filter(file=>file.task_id===task.id),rows=files.length?files.map(file=>`<div data-file="${esc(file.id)}" class="detail-row ${pending.has(file.id)?"pending":""}"${editable?` style="${EDITOR_FILE_GRID}"`:""}>${controller.fileLink(file)}<span class="file-size"${editable?' style="justify-self:end;white-space:nowrap"':""}>${controller.size(file.size)}</span>${editable?`<ha-icon-button class="editor-action remove ${pending.has(file.id)?"":"danger"}" label="${pending.has(file.id)?t("file.undo_remove"):t("file.remove")}" title="${pending.has(file.id)?t("common.undo"):t("common.remove")}" style="justify-self:end"><ha-icon icon="mdi:${pending.has(file.id)?"undo":"delete"}"></ha-icon></ha-icon-button>`:""}</div>`).join(""):`<small class="ht-content">${L.noFiles}</small>`;
  const content=editable?`<input type="file" multiple hidden><div class="file-list">${rows}</div><ha-button class="drop-zone" appearance="outlined"><ha-icon slot="start" icon="mdi:tray-arrow-up"></ha-icon>${t("file.drop")}</ha-button>`:`<div class="file-list">${rows}</div>`;
  return `<ha-expansion-panel class="files-box"><span slot="header" class="ht-label-medium">${L.files}</span><div class="details-content">${content}</div></ha-expansion-panel>`;
}

export function taskHistoryBoxHtml(controller,entries,{editable=false,pending=new Set(),status=""}={}){
  const rows=Array.isArray(entries)?(entries.length?entries.map(entry=>controller.historyRow(entry,editable)).join(""):`<small class="ht-content">${L.noHistory}</small>`):(status||t("common.loading"));
  return `<ha-expansion-panel class="history-box"><span slot="header" class="ht-label-medium">${L.history}</span><div class="details-content history-list ht-content">${rows}</div></ha-expansion-panel>`;
}
