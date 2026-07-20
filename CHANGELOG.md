# Changelog

## Unreleased

### Fixed

- Schedule dynamic entity additions in the dispatcher callback on Home Assistant's running event loop.

### Changed

- Compacted the list and task editor.
- Separated files and history into distinct task-editor sections and removed the group icon field from the editor.
- Replaced the temporary weekly type with a Todoist-style recurrence model: fixed or sliding calculation combined with daily, weekly, or monthly frequency.
- Added multiple weekday selection, monthly day/last-day selection, and right-aligned file actions.

### Added

- Initial Home Tasker Home Assistant integration.
- Expandable group/task panel with fixed/sliding filters, sorting, state and file pills.
- Group and task editors.
- Virtual group devices and due-state task entities.
- Task history, calendar-anchor scheduling, and task-owned uploads.
