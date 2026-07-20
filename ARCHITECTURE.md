# Architecture

Home Tasker deliberately starts with a small surface. The integration is local-only and permits one config entry.

## Model

- A group stores `id`, `name`, `manufacturer`, `model`, `icon`, and `description` and is represented by a virtual Home Assistant device.
- A task belongs to exactly one group and stores its name, description, due date, recurrence mode (`fixed` or `sliding`), frequency (`daily`, `weekly`, or `monthly`), interval, and calendar anchor.
- Fixed weekly schedules support multiple weekdays. Fixed monthly schedules support days 1–31 or the last day. Sliding schedules advance from the completion date.
- Before version 1.0, stored schema changes do not include compatibility normalization; development data may be reset.
- Every task exposes one problem `binary_sensor`; `on` means due.
- Attachments belong to one task. History entries retain `due_before` and `due_after` so deleting an entry restores the derived due date.

## Modules

- `store.py`: versioned persistence and serialized mutations
- `scheduler.py`: pure date arithmetic
- `websocket.py`: authenticated metadata API
- `http.py`: authenticated binary upload/download
- `binary_sensor.py`: task entities and virtual device metadata
- `frontend/panel.js`: dependency-free list and the group/task dialogs

The list has no recurrence filters or icon actions. Group actions appear at the bottom of expanded groups; clicking a task opens its editor, where completion and deletion are available.
Group headers show the number of due tasks as a red `N offen` pill.
Actions use native buttons styled with Home Assistant theme variables instead of unstable internal frontend components. Popup titles remain sticky while the dialog body scrolls.

Uploads live under `<config>/home_tasker/uploads`; metadata is stored in the versioned Home Assistant Store.
