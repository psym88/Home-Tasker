import { L, esc } from "./shared.js";
import { t } from "./localize.js";

export const EDITOR_FILE_GRID="display:grid;grid-template-columns:minmax(0,1fr) max-content 32px;gap:8px;align-items:center;min-height:40px";
const VIEWER_FILE_GRID="display:grid;grid-template-columns:minmax(0,1fr) max-content;gap:8px;align-items:center;min-height:40px";

export function taskDetailBoxHtml(title,content,{className="",expanded=false}={}){
  return `<ha-expansion-panel outlined${expanded?" expanded":""}${className?` class="${className}"`:""}><span slot="header">${esc(title)}</span><div class="details-content">${content}</div></ha-expansion-panel>`;
}

export function taskFilesBoxHtml(controller,task,{editable=false,pending=new Set()}={}){
  const files=controller.attachments.filter(file=>file.task_id===task.task_id),rows=files.length?files.map(file=>`<div data-file="${esc(file.attachment_id)}" class="file-row ${pending.has(file.attachment_id)?"pending":""}" style="${editable?EDITOR_FILE_GRID:VIEWER_FILE_GRID}">${controller.fileLink(file)}<span class="file-size" style="justify-self:end;white-space:nowrap">${controller.size(file.size)}</span>${editable?`<ha-icon-button class="editor-action remove ${pending.has(file.attachment_id)?"":"danger"}" label="${pending.has(file.attachment_id)?t("file.undo_remove"):t("file.remove")}" title="${pending.has(file.attachment_id)?t("common.undo"):t("common.remove")}" style="justify-self:end;--ha-icon-button-size:32px"><ha-icon icon="mdi:${pending.has(file.attachment_id)?"undo":"delete"}"></ha-icon></ha-icon-button>`:""}</div>`).join(""):(editable?"":`<small class="ht-content">${L.noFiles}</small>`);
  const content=editable?`<div class="attachment-drop-zone"><div class="file-list">${rows}</div><input type="file" multiple hidden><div class="upload-prompt"><ha-button class="choose-files" size="s" appearance="filled"><ha-icon slot="start" icon="mdi:folder-upload"></ha-icon>${esc(t("file.select"))}</ha-button><span>${esc(t("file.drop_secondary"))}</span></div></div>`:`<div class="file-list">${rows}</div>`;
  return taskDetailBoxHtml(L.files,content,{className:"files-box"});
}

export function taskHistoryBoxHtml(controller,entries,{editable=false,pending=new Set(),status=""}={}){
  const rows=Array.isArray(entries)?(entries.length?entries.map(entry=>controller.historyRow(entry,editable)).join(""):`<small class="ht-content">${L.noHistory}</small>`):(status||t("common.loading"));
  return taskDetailBoxHtml(L.history,`<div class="history-list ht-content">${rows}</div>`,{className:"history-box"});
}
