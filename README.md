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
- Expand a group to see its tasks. Compact group headers use Home Assistant's table background without hover, while transparent task rows use the primary background and gain a subtle text-color tint on hover. Group names use a larger heading style than the normal-weight task names, and a circular red badge shows the count of currently due tasks.
- Click a task row to open its read-only viewer with rendered Markdown, a concise due-date label, collapsible files and history, completion notes, and a completion action. Use the pencil at the right of the row to edit the task.
- Files can be uploaded by browsing or drag and drop. New uploads are discarded when the editor is closed without saving.
- History rows show the completion date, local time, user, and optional completion notes. Deleting a history entry restores the due date derived from the remaining history.
- The panel inherits Home Assistant theme typography, text colors, and button styling for consistent light, dark, and custom themes. Task rows have a transparent resting background and retain the original neutral hover treatment, as do icon actions.
- The editor uses consistent Home Assistant body typography throughout planning. It initially shows four unnumbered backend-calculated dates under "Due date preview" in normal text size and color. Weekdays and localized dates share one aligned, responsive two-column layout, ensuring every date starts at the same horizontal position below the recurrence description. "Show more" reveals one additional occurrence and retains that count when schedule options change. The final planning control presents "Optional start date" as a planning subtitle, places its selection below, and shows its removal action in the Home Assistant error color.
- Recurrence supports daily, weekly, monthly, and yearly rhythms. Calendar-based yearly tasks select a month and day, while completion-based yearly tasks advance from the actual completion date.
- Collapsible scheduling, file, and history boxes use compact internal spacing and clickable headers that match their visible area.
- Long attachment pills truncate only the base name so the file extension remains visible. Description fields can be resized vertically.

## Dashboard card

After the integration is loaded, Home Assistant automatically makes the **Home Tasker** card available in the dashboard card picker. The card lists tasks as flat rows ordered by due date; by default it shows tasks due today or earlier.

The visual card editor provides a fixed view or edit mode, a future due-date window, multi-select filters for groups and assignees (including unassigned tasks), and ascending or descending due-date sorting. Card settings are stored only in the dashboard configuration and do not change Home Tasker data. View mode omits all edit controls. Edit mode shows pencil and add actions only to administrators. Tasks render as separate rounded elements, with due dates colored orange for today, red when overdue, and green when upcoming.

All authenticated Home Assistant users can open task details and complete tasks with optional notes. Creating, editing, deleting, and changing history remain administrator-only operations.

## Recurrence

- **By calendar** schedules remain anchored to selected calendar days. Completing a task early keeps its upcoming occurrence, completing it on time advances once, and completing it late skips missed occurrences.
- **After completion** schedules advance from the actual completion date.
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
