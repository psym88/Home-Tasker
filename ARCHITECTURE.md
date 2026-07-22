# Architecture

Home Tasker is a local-push Home Assistant integration with one config entry. Persistent data is stored in Home Assistant; attachments live under `<config>/home_tasker/uploads`.

## Data model

- A **group** is represented by a virtual Home Assistant device.
- A **task** belongs to one group and stores its description, assignment, due date, optional start boundary, optional NFC tag, recurrence rule, attachments, and completion history.
- Calendar recurrence stays anchored to configured dates. Completion-based recurrence advances from the completion date.
- Before version 1.0, stored-schema changes need no compatibility migration.

## Home Assistant platforms

- Each task exposes a push-only problem `binary_sensor`; `on` means due. The static attribute `home_tasker_entity_type: task` allows reliable aggregation without depending on entity IDs.
- One read-only `calendar` entity exposes current and projected task due dates.
- Group deletion removes its task entities and device-registry entry. Orphan cleanup is limited to the `binary_sensor` domain.
- Task state refreshes after mutations and at local midnight.

## Backend

- `store.py`: persistence and serialized mutations
- `models.py`: stored data structures
- `scheduler.py`: recurrence calculations
- `websocket.py`: authenticated task and metadata API
- `http.py`: authenticated attachments and ZIP import/export
- `binary_sensor.py`: task entities and group devices
- `calendar.py`: read-only due-date calendar
- `nfc.py`: tag-scan handling and completion attribution
- `events.py`: the public change-event contract shared by backend and frontend consumers
- `config_flow.py` and `__init__.py`: setup and integration lifecycle

Import validates a current-format archive before clearing and replacing all stored Home Tasker data. No legacy archive fallback is maintained.

## Frontend

The frontend is split into native ES modules under `custom_components/home_tasker/frontend`:

- `main.js`: shared controller and sidebar panel
- `dashboard-card.js`: Lovelace card and visual editor
- `task-list.js`: grouped and flat task rendering
- `task-editor.js`, `task-viewer.js`, `group-editor.js`: workflows
- `native-*-dialog.js`: Home Assistant adaptive-dialog hosts
- `styles.js`, `shared.js`, `dialogs.js`, `action-menu.js`: shared UI primitives
- `localize.js`: frontend localization

The sidebar panel and dashboard card share the same controller, viewer/editor workflows, typography, collapsible sections, icons, and theme rules. Dialogs use Home Assistant's composed `show-dialog` contract. Attachments are real signed anchors whose click handler opens the native preview dialog.

The frontend loads an initial snapshot and reloads it from `home_tasker_event`. The same event updates task entities and the calendar after stored mutations and at local midnight; no dispatcher, entity fingerprint, or periodic polling is used. A task-level `due` action is emitted once when a task crosses from not due to due, including at the local date rollover, without replaying due events at startup or archive import.

## Security and permissions

WebSocket and HTTP endpoints require an authenticated Home Assistant user. All signed-in users can manage tasks and groups; only administrators can open the sidebar panel. Dashboard edit controls are governed by the card configuration. Attachment paths are task-scoped and served through signed URLs.

## Tests and releases

- Backend tests: `pytest`
- Frontend tests: `node --test tests/frontend/*.test.mjs`
- Release versions must match in `manifest.json`, `const.py`, and `frontend/panel.js`.
- Development releases are tagged from `dev` and published as GitHub pre-releases.
