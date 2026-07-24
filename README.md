# Home Tasker

Home Tasker adds recurring household tasks to Home Assistant. Tasks can be assigned, scheduled, completed with notes, and linked to files or NFC tags.

[![Open your Home Assistant instance and add this repository to HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=psym88&repository=Home-Tasker&category=integration)

## Features

- Daily, weekly, monthly, and yearly recurring tasks
- Calendar-based schedules or intervals after completion
- Home Assistant user and label assignments, notes, history, and attachments
- Optional NFC tag completion
- Sidebar panel and configurable dashboard card
- A native Home Tasker to-do list, due-task summary sensor, and read-only task calendar
- Home Assistant events for task, history, and attachment changes
- ZIP backup and restore
- English and German interface

## Installation

Home Tasker requires Home Assistant 2026.7.0 or newer.

1. Use the button above, or add `https://github.com/psym88/Home-Tasker` to HACS as an **Integration** repository.
2. Install Home Tasker and restart Home Assistant.
3. Open **Settings → Devices & services → Add integration** and select **Home Tasker**.

Only one Home Tasker configuration entry can be created.

### Removal

1. Open **Settings → Devices & services**, select **Home Tasker**, and delete the integration entry.
2. Remove Home Tasker from HACS.
3. Restart Home Assistant.

Removing the integration does not delete exported backups. Home Tasker data in `<config>/.storage/home_tasker` and attachments in `<config>/home_tasker/uploads` can be removed manually if they are no longer needed.

## Usage

Administrators can open **Home Tasker** in the sidebar. Use **+ Add task** to create a task. Select a task to view and complete it; use its three-dot menu to edit or delete it.

The task table shows Label directly after Task and supports search, sorting, grouping by labels, recurrence, or assignee, and independent filters for those same dimensions.

Schedules can repeat by calendar or from the last completion. The optional start date limits when a recurrence begins. Files are managed in the task editor and supported formats open in an in-panel preview dialog.

To complete a task with NFC, create a tag under **Settings → Tags** and assign it in the task editor. One tag can be assigned to only one task.

### Dashboard card

Add the **Home Tasker** card from the dashboard card picker. Its visual editor controls view/edit mode, the due-date range, and assignee filters. Open panels and cards update immediately from Home Tasker events.

### Backup and restore

Open **Settings** above the task list and expand **Backup**. Export creates a ZIP archive containing all Home Tasker data and attachments. Import validates the archive and adds only tasks with new IDs together with their history and conflict-free attachments. Existing tasks and files are never overwritten.

## Home Assistant entities

All tasks are exposed as items of the native `todo.home_tasker` entity. Home Assistant can create, edit, complete, and delete these items using its standard to-do dashboard, actions, and triggers. Item `uid`, `summary`, `description`, and `due` map to Home Tasker's `task_id`, `task_name`, `task_description`, and `task_due`. `task_due` accepts a native ISO date for an all-day task or an ISO datetime for an exact due time. Recurrence, user and label assignments, NFC tags, attachments, and completion history remain in Home Tasker's store.

The `sensor.home_tasker_tasks_due` entity counts tasks whose due date or due time has been reached. The state of `todo.home_tasker` itself is Home Assistant's standard count of all incomplete items. Calendar, todo, and due sensor entities belong to the shared **Home Tasker** device.

Example badge for [Navbar Card](https://github.com/joseluis9595/lovelace-navbar-card):

```yaml
badge:
  count: |
    [[[
      return Number(states['sensor.home_tasker_tasks_due']?.state || 0);
    ]]]
  show: |
    [[[
      return Number(states['sensor.home_tasker_tasks_due']?.state || 0) > 0;
    ]]]
```

The read-only **Home Tasker** calendar exposes current and projected task due dates.

## Home Assistant events

Home Tasker fires `home_tasker_event` after every stored change and when a task reaches its due time. Automations can filter its `resource_type` and `action` data. Resource types are `task`, `history`, `attachment`, and `archive`; actions are `created`, `updated`, `deleted`, `completed`, `imported`, and `task_due` where applicable.

To receive a notification when a task becomes due, create an automation, open **Edit in YAML**, and paste:

```yaml
alias: Home Tasker task is due
triggers:
  - trigger: event
    event_type: home_tasker_event
    event_data:
      resource_type: task
      action: task_due
actions:
  - action: notify.notify
    data:
      title: Home Tasker
      message: "{{ trigger.event.data.resource_name }} is due."
```

Every event includes `resource_id` when the changed resource has one. Task events also include `resource_name`; related identifiers such as `task_id` are included when available.

## Data and support

Home Tasker stores task data locally in Home Assistant and attachments under `<config>/home_tasker/uploads`. It does not send task data to an external service.

- [Issues and feature requests](https://github.com/psym88/Home-Tasker/issues)
- [Release history](https://github.com/psym88/Home-Tasker/releases)
- [Architecture](ARCHITECTURE.md)
- [MIT License](LICENSE)
