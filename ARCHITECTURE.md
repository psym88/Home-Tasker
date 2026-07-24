# Architecture

Home Tasker is a local-push Home Assistant integration with one config entry. Persistent data is stored in Home Assistant; attachments live under `<config>/home_tasker/uploads`.

## Data model

- A **task** stores its description, assignment, native date-or-datetime `task_due` value, optional start boundary, optional NFC tag, recurrence rule, attachments, and completion history.
- Calendar recurrence stays anchored to configured dates. Completion-based recurrence advances from the completion date.
- Before version 1.0, stored-schema changes need no compatibility migration.

## Home Assistant platforms

- Tasks are items of one push-only `todo.home_tasker` entity. Standard item fields map to the task ID, name, description, due value, and open/completed status.
- `sensor.home_tasker_tasks_due` remains a separate summary because a to-do entity's native state counts every incomplete item, not only due items.
- One read-only `calendar` entity exposes current and projected task due dates.
- Calendar, todo, and due sensor entities share one Home Tasker service device.
- A single timer tracks the nearest future `task_due`, fires one `task_due` event per matching task, and then schedules the next due time. Task mutations rebuild that timer.

## Backend

- `store.py`: persistence and serialized mutations
- `models.py`: typed runtime data attached to the config entry
- `scheduler.py`: recurrence calculations
- `due.py`: shared date/datetime parsing and the single due-event timer
- `websocket.py`: authenticated task and metadata API
- `http.py`: authenticated attachments and ZIP import/export
- `todo.py`: native task-list entity and standard item mutations
- `sensor.py`: due-task summary entity
- `calendar.py`: read-only due-date calendar
- `nfc.py`: tag-scan handling and completion attribution
- `events.py`: public Home Tasker event helper
- `config_flow.py` and `__init__.py`: setup and integration lifecycle

Import validates a current-format archive before clearing and replacing all stored Home Tasker data. No legacy archive fallback is maintained.

## Frontend

The frontend is split into native ES modules under `custom_components/home_tasker/frontend`:

- `main.js`: shared data and workflow controller used by the panel and card
- `dashboard-card.js`: Lovelace card and visual editor
- `task-list.js`: sidebar table adapter, flat row mapping, filters, and HA table configuration
- `filter-category.js`: filter categories for the sidebar table
- `task-editor.js`: task editor workflow
- `task-detail-boxes.js`: reusable file and history sections for task dialogs
- `native-*-dialog.js`: Home Assistant adaptive-dialog hosts, including the task viewer
- `styles.js`, `shared.js`, `dialogs.js`, and `action-menu.js`: shared UI contracts and primitives
- `localize.js`: frontend localization

The sidebar panel maps backend tasks to flat rows and delegates its toolbar, search, sorting, grouping, and table rendering to Home Assistant's internal `hass-tabs-subpage-data-table` and `ha-data-table` components. Filters reduce the row data before it is passed to the table. The dashboard card keeps its separate compact task presentation.

The sidebar panel and dashboard card share the same controller and task viewer/editor workflows. Dialogs use Home Assistant's composed `show-dialog` contract and `ha-adaptive-dialog`; shared file and history sections are produced by `task-detail-boxes.js`. Attachments are signed anchors whose click handler opens the integration's preview dialog through the same native dialog contract.

Frontend development follows a native-first rule: use Home Assistant components and interaction contracts before adding custom UI. Custom CSS is limited to structural layout that HA components do not provide; visual values use Home Assistant CSS variables and design tokens. No external UI or table library is used.

The frontend loads an initial snapshot and reloads it from `home_tasker_event`. The same event updates the to-do list, summary sensor, and calendar immediately after stored mutations and due-time transitions; no dispatcher, entity fingerprint, or polling is used.

## Security and permissions

WebSocket and HTTP endpoints require an authenticated Home Assistant user. All signed-in users can manage tasks; only administrators can open the sidebar panel. Dashboard edit controls are governed by the card configuration. Attachment paths are task-scoped and served through signed URLs.

## Tests and releases

- Backend tests: `pytest`
- Frontend tests: `node --test tests/frontend/*.test.mjs`
- Release versions must match in `manifest.json`, `const.py`, and `frontend/panel.js`.
- Development releases are tagged from `dev` and published as GitHub pre-releases.
