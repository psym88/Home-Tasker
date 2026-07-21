# Architecture

Home Tasker deliberately has a small surface. The integration is local-only and permits one config entry.

## Model

- A group stores `id`, `name`, `manufacturer`, `model`, and `description` and is represented by a virtual Home Assistant device. A legacy/API-only `icon` value is retained but is not exposed by the panel. Group names are unique when compared case-insensitively.
- A task belongs to exactly one group and stores its name, description, due date, recurrence mode (`fixed` or `sliding`), frequency (`daily`, `weekly`, or `monthly`), interval, and calendar anchor.
- Fixed weekly schedules support multiple weekdays. Fixed monthly schedules support days 1–31 or the last day. Sliding schedules advance from the completion date, including the completion day for monthly schedules.
- Before version 1.0, stored schema changes do not include compatibility normalization; development data may be reset.
- Every task exposes one problem `binary_sensor`; `on` means due. Deleting tasks or groups also removes their entity/device registry entries.
- Attachments belong to one task. Their browser links are pre-signed through admin-only WebSocket commands and rendered as native anchors for authenticated mobile/browser access. History entries retain `due_before` and `due_after` so deleting an entry restores the derived due date. An explicit due-date edit is applied after pending history deletions and therefore wins.

## Modules

- `store.py`: versioned persistence and serialized mutations
- `scheduler.py`: pure date arithmetic
- `websocket.py`: authenticated metadata API
- `http.py`: authenticated binary upload/download
- `binary_sensor.py`: task entities and virtual device metadata
- `frontend/panel.js`: dependency-free list and the group/task dialogs

The list has no recurrence filters. Group editing appears as a pencil action at the right of the group header; deletion is available at the lower left of the group editor. Clicking a task opens a read-only viewer with rendered Markdown, a human-readable schedule, attachments, history, and completion. The blue pencil action at the right of a task row opens its editor, where deletion is available.
Group headers show the number of due tasks as a red numeric pill.
Actions use native buttons styled with Home Assistant theme variables instead of unstable internal frontend components. Popup titles remain sticky while the dialog body scrolls.

The backend supplies Home Assistant's current local date so sensors, relative dates, and the frontend agree around midnight. The panel refreshes visible data every 30 seconds and retries automatically after load failures. Attachment URLs are returned in bulk instead of requiring one WebSocket request per file.

Uploads live under `<config>/home_tasker/uploads`; metadata is stored in the versioned Home Assistant Store.
