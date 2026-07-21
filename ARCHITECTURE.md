# Architecture

Home Tasker deliberately has a small surface. The integration is local-only and permits one config entry.

## Model

- A group stores `id`, `name`, `manufacturer`, `model`, and `description` and is represented by a virtual Home Assistant device. A legacy/API-only `icon` value is retained but is not exposed by the panel. Group names are unique when compared case-insensitively.
- A task belongs to exactly one group and stores its name, description, calculated due date, optional start boundary, recurrence mode (`fixed` or `sliding`), frequency (`daily`, `weekly`, `monthly`, or `yearly`), interval, and calendar anchor.
- Fixed weekly schedules support multiple weekdays. Fixed monthly schedules support days 1–31 or the last day. Completing a fixed task before its due date preserves the upcoming occurrence; completing it on time advances once, while late completion skips missed occurrences. Sliding schedules advance from the completion date, including the completion day for monthly schedules.
- Before version 1.0, stored schema changes do not include compatibility normalization; development data may be reset.
- Every task exposes one problem `binary_sensor`; `on` means due. The sensors are push-only (polling disabled) and refresh on data mutations and at local midnight so the due state flips at the date rollover. Deleting tasks or groups also removes their entity/device registry entries.
- Attachments belong to one task. Their browser links are pre-signed through admin-only WebSocket commands and rendered as native anchors for authenticated mobile/browser access. History entries retain `due_before`, `due_after`, the recording timestamp, user, and optional completion notes so deleting an entry restores the derived due date.

## Modules

- `store.py`: versioned persistence and serialized mutations
- `scheduler.py`: pure date arithmetic
- `websocket.py`: authenticated metadata API
- `http.py`: authenticated binary upload/download
- `binary_sensor.py`: task entities and virtual device metadata
- `frontend/panel.js`: lightweight ES-module entry point and custom-element registration
- `frontend/main.js`: panel state, Home Assistant communication, shared formatting, and feature coordination
- `frontend/task-list.js`: grouped panel list plus reusable flat due-date sorting for a future dashboard card
- `frontend/task-editor.js`, `task-viewer.js`, and `group-editor.js`: task and group workflows
- `frontend/dialogs.js`, `shared.js`, and `styles.js`: dialog primitives, escaping, Markdown helpers, and shared panel styling

The list has no recurrence filters. Following Home Assistant's data-table pattern, the group container uses `--data-table-background-color`, group headers use `--primary-background-color` without hover, and transparent task rows add a four-percent primary-text tint only on hover. Group headers share task-row padding and show the number of due tasks in a circular red badge. Group editing appears as a pencil action at the right of the group header; deletion is available at the lower left of the group editor. Clicking a task opens a read-only viewer with rendered Markdown, a human-readable schedule, collapsible attachments and history, optional completion notes, and completion. The blue pencil action at the right of a task row opens its editor, where deletion is available. The editor labels recurrence as "By calendar" or "After completion", previews four backend-calculated due dates initially, and reveals additional occurrences one at a time. Its optional start-date control uses the same subtitle hierarchy as the other planning controls, with the selection action below and a red removal action. Viewer and editor history rows show date, local time, user, and notes; only the editor exposes the delete action.
The viewer labels the currently calculated date concisely as "Due date".
Group headers show the number of due tasks as a red numeric pill.
Actions use native buttons styled with Home Assistant theme variables instead of unstable internal frontend components. Popup titles remain sticky while the dialog body scrolls.
Typography follows Home Assistant font, size, weight, line-height, and color variables. The due-date preview and other supporting text use the normal body size. Its weekday and date values render in one shared responsive, left-aligned two-column grid below the recurrence description, so column widths are consistent across every row. Main-list group names use the large heading size, while task names use the normal body size and weight. Action buttons share a 44-pixel minimum control height, while icon actions use a matching square footprint.
Collapsible boxes remove redundant vertical padding and keep the clickable header aligned with its visible area. The optional start boundary is normal body text with only its selection action triggering a visually hidden native date input; a clear action appears when populated. The editor initially requests four unnumbered dates under a preview subtitle and increments the backend sequence count by one for each "Show more" action; this count is retained across schedule-option changes. Recurrence mode, rhythm, and preview subtitles share a larger Home Assistant theme-aware text style. Preview dates combine a localized weekday with the locale-specific numeric date. The backend uses the same scheduler for previews, task creation, schedule updates, and persisted completion dates. Task rows use an explicitly transparent resting background and the original neutral row hover. Icon actions retain circular, neutral, theme-aware hover and focus treatments.

The backend supplies Home Assistant's current local date so sensors, relative dates, and the frontend agree around midnight. The panel refreshes visible data every 30 seconds and retries automatically after load failures. Attachment URLs are returned in bulk instead of requiring one WebSocket request per file.

Uploads live under `<config>/home_tasker/uploads`; metadata is stored in the versioned Home Assistant Store.
