# Changelog

## Unreleased

### Added

- Apply the selected name/state sort order to tasks inside every group.
- Initial Home Tasker Home Assistant integration.
- Expandable group/task panel with fixed/sliding filters, sorting, state and file pills.
- Group and task editors.
- Virtual group devices and due-state task entities.
- Task history, calendar-anchor scheduling, and task-owned uploads.

### Fixed

- Schedule dynamic entity additions in the dispatcher callback on Home Assistant's running event loop.
- Keep the task editor open and refresh its due date/history after completion.

### Changed

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
