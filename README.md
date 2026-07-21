# Home Tasker

Home Tasker brings recurring household tasks into Home Assistant. Organize tasks in groups, assign them to Home Assistant users, track due dates and completion history, and attach useful files or notes.

[![Open your Home Assistant instance and add this repository to HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=psym88&repository=Home-Tasker&category=integration)

## Features

- Daily, weekly, monthly, and yearly recurring tasks
- Calendar-based schedules or intervals based on the last completion
- Task groups and assignment to Home Assistant users
- Completion notes, history, and file attachments
- A dedicated Home Tasker panel for managing tasks
- A configurable dashboard card for a focused task list
- Home Assistant entities for automations and notifications
- Local storage inside your Home Assistant configuration

## Requirements

- Home Assistant 2026.7.0 or newer
- HACS for the recommended installation method

## Installation

### Install with HACS

1. Select the **Open your Home Assistant** button above.
2. Confirm that you want to open your Home Assistant instance.
3. Add **Home Tasker** as a custom integration repository.
4. Install **Home Tasker** in HACS.
5. Restart Home Assistant.

### Add the repository manually

1. Open **HACS → Integrations**.
2. Open the menu in the upper-right corner and select **Custom repositories**.
3. Enter `https://github.com/psym88/Home-Tasker` and select **Integration** as the category.
4. Add the repository, install **Home Tasker**, and restart Home Assistant.

## Setup

1. Open **Settings → Devices & services**.
2. Select **Add integration** and search for **Home Tasker**.
3. Complete the setup. Home Tasker then appears in the Home Assistant sidebar.

Only one Home Tasker configuration entry can be created.

## Getting started

### Create and organize tasks

Select **+ Add task** at the top of the Home Tasker panel. Choose an existing group or enter a new group name, then configure the task, assignment, and schedule. You can also add a task directly at the end of an expanded group.

Groups can be expanded to show their tasks. The badge beside a group shows how many of its tasks are currently due.

### View, complete, and manage tasks

Select a task to open its details. From there you can review its description, schedule, files, and history, and complete it with an optional note.

Administrators can use the three-dot menu beside a task or group to edit or delete it. Files can be attached from the task editor by selecting them or using drag and drop. Supported files open in a Home Assistant preview dialog.

### Recurring schedules

- **By calendar** keeps a task anchored to selected calendar days. Completing it early preserves the upcoming occurrence; late completion skips missed occurrences.
- **After completion** calculates the next due date from the day the task was completed.
- Daily schedules use a number of days.
- Weekly calendar schedules can use multiple weekdays and multi-week intervals.
- Monthly calendar schedules can use days 1–31 or the last day of the month.
- Yearly calendar schedules use a selected month and day.

The task editor previews upcoming due dates before you save the schedule.

## Dashboard card

After Home Tasker is loaded, the **Home Tasker** card is available in the dashboard card picker. By default, it shows overdue tasks and tasks due today, with the oldest task first.

The visual card editor lets you configure:

- **View mode**, which shows tasks without management actions
- **Edit mode**, which adds task creation and edit/delete actions for administrators
- How many upcoming days to include, or no due-date limit
- Group and assignee filters, including unassigned tasks
- Whether the outer card background and frame are shown

Select a task in the card to open its details and complete it. Card settings are stored only in that dashboard and do not change your tasks or integration settings.

## Permissions

All signed-in Home Assistant users can view tasks, open attachments and history, and complete tasks with optional notes. Only administrators can create, edit, or delete tasks and groups, remove history entries, and use the dashboard card's edit controls.

## Home Assistant entities

Each group is represented as a Home Assistant device. Every task provides a problem `binary_sensor`; it is `on` while the task is due. Assignment and schedule information is available as entity attributes for use in automations and notifications.

## Data and privacy

Home Tasker stores its data locally in your Home Assistant configuration. Attachments are stored under `<config>/home_tasker/uploads`. No task data is sent to an external service by Home Tasker.

## Help and project information

- Report bugs or request features in the [GitHub issue tracker](https://github.com/psym88/Home-Tasker/issues).
- See the [changelog](CHANGELOG.md) for release history.
- Technical contributors can find implementation details in the [architecture documentation](ARCHITECTURE.md).
- Home Tasker is distributed under the [MIT License](LICENSE).
