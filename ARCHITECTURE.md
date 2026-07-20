# Architecture

Home Tasker deliberately starts with a small surface. The integration is local-only and permits one config entry.

## Model

- A group stores `id`, `name`, `manufacturer`, `model`, `icon`, and `description` and is represented by a virtual Home Assistant device.
- A task belongs to exactly one group and stores its name, description, due date, recurrence mode (`fixed` or `sliding`), interval, unit, and calendar anchor.
- Every task exposes one problem `binary_sensor`; `on` means due.
- Attachments belong to one task. History entries retain `due_before` and `due_after` so deleting an entry restores the derived due date.

## Modules

- `store.py`: versioned persistence and serialized mutations
- `scheduler.py`: pure date arithmetic
- `websocket.py`: authenticated metadata API
- `http.py`: authenticated binary upload/download
- `binary_sensor.py`: task entities and virtual device metadata
- `frontend/panel.js`: dependency-free list and the group/task dialogs

Uploads live under `<config>/home_tasker/uploads`; metadata is stored in the versioned Home Assistant Store.

