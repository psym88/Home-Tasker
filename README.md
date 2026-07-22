# Home Tasker

Home Tasker adds recurring household tasks to Home Assistant. Tasks can be grouped, assigned, scheduled, completed with notes, and linked to files or NFC tags.

[![Open your Home Assistant instance and add this repository to HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=psym88&repository=Home-Tasker&category=integration)

## Features

- Daily, weekly, monthly, and yearly recurring tasks
- Calendar-based schedules or intervals after completion
- Groups, Home Assistant user assignments, notes, history, and attachments
- Optional NFC tag completion
- Sidebar panel and configurable dashboard card
- Due-task binary sensors and a read-only task calendar
- Home Assistant events for task, group, history, and attachment changes
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

Open **Home Tasker** in the sidebar. Use **+ Add task** to create a task and either select an existing group or enter a new group name. Select a task to view and complete it; use its three-dot menu to edit or delete it.

Schedules can repeat by calendar or from the last completion. The optional start date limits when a recurrence begins. Files are managed in the task editor and supported formats open in Home Assistant's preview dialog.

To complete a task with NFC, create a tag under **Settings → Tags** and assign it in the task editor. One tag can be assigned to only one task.

### Dashboard card

Add the **Home Tasker** card from the dashboard card picker. Its visual editor controls view/edit mode, the due-date range, and group or assignee filters. Open panels and cards update immediately from Home Tasker events.

### Backup and restore

Open **Settings** above the task list and expand **Import / Export**. Export creates a ZIP archive containing all Home Tasker data and attachments. Import validates the archive, clears the current data, and replaces it after confirmation.

## Home Assistant entities

Each group is a Home Assistant device. Every task provides a problem `binary_sensor` that is `on` while due and exposes `home_tasker_entity_type: task`.

Example template sensor for the number of due and overdue tasks:

```yaml
template:
  - sensor:
      - name: "Home Tasker due tasks"
        unique_id: home_tasker_due_tasks
        icon: mdi:clipboard-alert-outline
        state: >
          {{ states.binary_sensor
             | selectattr('attributes.home_tasker_entity_type', 'eq', 'task')
             | selectattr('state', 'eq', 'on')
             | list
             | count }}
```

Example badge for [Navbar Card](https://github.com/joseluis9595/lovelace-navbar-card):

```yaml
badge:
  count: |
    [[[
      return Object.keys(states).filter(id =>
        id.startsWith('binary_sensor.') &&
        states[id].attributes.home_tasker_entity_type === 'task' &&
        states[id].state === 'on'
      ).length;
    ]]]
  show: |
    [[[
      return Object.keys(states).filter(id =>
        id.startsWith('binary_sensor.') &&
        states[id].attributes.home_tasker_entity_type === 'task' &&
        states[id].state === 'on'
      ).length > 0;
    ]]]
```

The read-only **Home Tasker** calendar exposes current and projected task due dates.

### Due-task notifications

Home Tasker fires one `home_tasker_task_due` event when a task crosses from not due to due. This can happen at local midnight or when creating or changing a task makes it immediately due. Create a new automation in Home Assistant, open **Edit in YAML**, and paste:

```yaml
alias: Home Tasker task is due
triggers:
  - trigger: event
    event_type: home_tasker_task_due
actions:
  - action: notify.notify
    data:
      title: Home Tasker
      message: "{{ trigger.event.data.task_name }} is due."
```

The event contains `task_id`, `task_name`, `group_id`, `due_date`, and `source`. It is not replayed when Home Assistant starts or when an archive is imported, and changes to an already-due task do not fire it again.

## Home Assistant events

Home Tasker fires `home_tasker_event` after every stored change. Automations can filter its `resource_type` and `action` data. Resource types are `task`, `group`, `history`, `attachment`, and `archive`; actions are `created`, `updated`, `deleted`, `completed`, and `imported` where applicable.

To receive a notification when any task is completed, create another automation, open **Edit in YAML**, and paste:

```yaml
alias: Home Tasker task completed
triggers:
  - trigger: event
    event_type: home_tasker_event
    event_data:
      resource_type: task
      action: completed
actions:
  - action: notify.notify
    data:
      message: "Task {{ trigger.event.data.resource_name }} was completed."
```

Every event includes `resource_id` when the changed resource has one. Task and group events also include `resource_name`; related identifiers such as `group_id` or `task_id` are included when available. A system refresh is also emitted at local midnight with `resource_type: system`, `action: refreshed`, and `reason: local_midnight`.

## Data and support

Home Tasker stores task data locally in Home Assistant and attachments under `<config>/home_tasker/uploads`. It does not send task data to an external service.

- [Issues and feature requests](https://github.com/psym88/Home-Tasker/issues)
- [Release history](https://github.com/psym88/Home-Tasker/releases)
- [Architecture](ARCHITECTURE.md)
- [MIT License](LICENSE)
