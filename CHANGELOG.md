# Changelog

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
