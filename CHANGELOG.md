# Changelog

## 0.2.20

- Tasks können in der Listenansicht per Drag-and-drop auf eine andere Gruppenzeile verschoben werden.
- Auf Touch-Geräten startet das Verschieben durch kurzes Gedrückthalten einer Task-Zeile.
- Das Ziel wird hervorgehoben und nach dem Verschieben aufgeklappt.

## 0.2.19

- Beim Wechsel der Task-Gruppe wird die Entity-ID passend zum neuen virtuellen Gerät kollisionsfrei neu generiert.
- Die stabile Unique-ID der Entität bleibt dabei erhalten.

## 0.2.18

- Der globale Eintrag „Gruppe hinzufügen“ wurde durch „Task hinzufügen“ ersetzt.
- Der Task-Editor unterstützt Gruppen-Autovervollständigung, das Erstellen neuer Gruppen und die Fallback-Gruppe „Tasks“ bei leerer Eingabe.
- Die Gruppenzuweisung bestehender Tasks kann geändert werden; ihre Home-Assistant-Entität wird dem passenden virtuellen Gerät zugeordnet.

## 0.2.17

- Tasks ohne Gruppenzuweisung werden der automatisch angelegten Fallback-Gruppe „Tasks“ zugeordnet.
- Die Fallback-Gruppe bleibt ein normales virtuelles Home-Assistant-Gerät, damit Task-Entitäten für Automationen verfügbar sind.

## 0.2.16

- Der Editor ist mit Abstand zum oberen Bildschirmrand fixiert, damit aufklappende Bereiche ihn nicht mehr vertikal verschieben.

## 0.2.15

- Planung, Dateien und Verlauf im Task-Editor sind standardmäßig eingeklappt.
- Die drei Bereiche lassen sich über einen Chevron im Box-Titel auf- und zuklappen.

## Unreleased

### Added

- Added pre-signed authenticated attachment links that open natively in browsers and the iOS Companion App.
- Apply the selected name/state sort order to tasks inside every group.
- Initial Home Tasker Home Assistant integration.
- Expandable group/task panel with fixed/sliding filters, sorting, state and file pills.
- Group and task editors.
- Virtual group devices and due-state task entities.
- Task history, calendar-anchor scheduling, and task-owned uploads.

### Fixed

- Remove deleted task entities and orphaned group devices from Home Assistant's registries.
- Render task entity icons with Home Assistant's current state-icon component.
- Schedule dynamic entity additions in the dispatcher callback on Home Assistant's running event loop.
- Keep the task editor open and refresh its due date/history after completion.

### Changed

- Made description fields non-resizable and renamed the visible due-date field to task date.
- Boxed the scheduling controls and renamed fixed/sliding recurrence to task-date/completion-date wording.
- Limited sorting to name and due date, removed header totals, truncated long filenames, and removed the empty validation gap above files.
- Replaced the file browse link with a visible clickable drop zone and distributed weekday buttons evenly across the full mobile width.
- Balanced task-row spacing and replaced all task-editor delete text/emoji controls with red MDI delete icons.
- Centered task icons in a padded leading column, hid zero-count open pills, and replaced group edit/delete text actions with icons.
- Removed the task-row indent and total-task pill, and shortened the open-task pill to its number.
- Added expansion chevrons to group rows and the original Home Assistant entity icon to each task row.
- Moved group editing to the right side of the group header and group deletion to the lower-left corner of the group editor.
- Match list and task-editor actions to the Save/Cancel button treatment; delete uses the neutral button with red text.
- Show each group's due-task count as a red `N offen` pill.
- Display attachment counts as `N Dateien` and remove added sizing/padding from text action buttons.
- Keep popup titles visible while their content scrolls.
- Render mobile-friendly HA-themed native action buttons with 44-pixel touch targets.
- Removed recurrence filter chips and all list action icons.
- Made task rows open the editor and moved task completion/deletion into that editor.
- Moved group edit/delete actions to the bottom of expanded groups and added list hover states.
- Replaced the attachment icon pill with a text label.
- Compacted the list and task editor.
- Separated files and history into distinct task-editor sections and removed the group icon field from the editor.
- Replaced the temporary weekly type with a Todoist-style recurrence model: fixed or sliding calculation combined with daily, weekly, or monthly frequency.
- Added multiple weekday selection, monthly day/last-day selection, and right-aligned file actions.
- Keep panel and integration versions aligned and default new tasks to sliding recurrence.
- Drop pre-1.0 compatibility normalization for superseded development schemas.
