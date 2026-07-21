# Home Tasker

Home Tasker is a local Home Assistant custom integration for recurring household tasks.

## Requirements

- Home Assistant 2026.7.0 or newer
- HACS for the recommended installation method

## Installation

1. Add this repository to HACS as a custom integration repository.
2. Install **Home Tasker**.
3. Restart Home Assistant.
4. Add the integration under **Settings → Devices & services**.

Only one Home Tasker config entry can be created.

## Usage

- Use the global **Add task** button to create a task. Enter an existing group name or create a new group directly from the task editor.
- Expand a group to see its tasks. The red number is the count of currently due tasks.
- Click a task row to open its read-only viewer with rendered Markdown, schedule, collapsible files and history, completion notes, and a completion action. Use the blue pencil at the right of the row to edit the task.
- Files can be uploaded by browsing or drag and drop. New uploads are discarded when the editor is closed without saving.
- History rows show the completion date, local time, user, and optional completion notes. Deleting a history entry recalculates the derived due date. If the due date is edited in the same save operation, the explicitly entered date wins.
- The panel inherits Home Assistant theme typography, text colors, and button styling for consistent light, dark, and custom themes.
- The editor schedule summary shows the first six due dates without trailing punctuation. All future dates are calculated as a generic sequence by the backend scheduler, beginning with a completion today.
- Collapsible scheduling, file, and history boxes use compact internal spacing and clickable headers that match their visible area.
- Long attachment pills truncate only the base name so the file extension remains visible. Description fields can be resized vertically.

## Recurrence

- **Fixed** schedules remain anchored to their calendar. Completing an overdue task skips missed occurrences and selects the next future occurrence.
- **Sliding** schedules advance from the completion date.
- Daily schedules advance by a number of days.
- Weekly fixed schedules support multiple weekdays and multi-week intervals.
- Monthly fixed schedules support days 1–31 or the last day. Dates such as day 31 are clamped to the last available day of shorter months.
- Monthly sliding schedules use the completion day as the next monthly anchor.

## Home Assistant entities

- Every group is represented by one virtual Home Assistant device.
- Every task exposes one problem `binary_sensor`; `on` means that the task is due.
- Task assignment and schedule fields are available as entity attributes.

## Data storage

Metadata is stored in Home Assistant's versioned Store. Uploads live under `<config>/home_tasker/uploads`. All data stays inside the Home Assistant configuration directory.

## Development and releases

Release notes and changelog entries must always be written in English. Keep the versions in `manifest.json`, `const.py`, and `frontend/panel.js` aligned.

Report problems through the [GitHub issue tracker](https://github.com/psym88/Home-Tasker/issues).
