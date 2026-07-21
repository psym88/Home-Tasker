# Changelog

All release notes and changelog entries are written in English.

## 0.2.41

### Changed

- Present the optional start date as normal body text with only the selection action clickable.
- Use normal Home Assistant body typography for "Show more".
- Remove occurrence numbering from the due-date preview.
- Apply a larger shared Home Assistant subtitle style to recurrence mode, rhythm, and due-date preview labels.

## 0.2.40

### Changed

- Show the optional start date directly under its heading without a collapsible box.
- Add a "Due date preview" heading and remove the repeated "Due date" label from occurrence rows.
- Preserve the expanded occurrence count when schedule options change.

## 0.2.39

### Changed

- Add the missing period after numeric days in monthly schedule descriptions.
- Place "Show more" directly beneath the due-date list.
- Keep the optional start date as the final planning control, immediately before the generated schedule text.
- Replace the visible start-date input with subtle text that opens the native date picker and retains a clear action.

## 0.2.38

### Changed

- Shorten the task viewer schedule label from "Next due date" to "Due date".

## 0.2.37

### Changed

- Show four due dates by default and reveal one additional occurrence per "Show more" action.
- Prefix preview dates with a localized weekday while preserving the user's locale-specific date order and separators.
- Place the optional start date as the final option inside the planning box.
- Display yearly day and month selectors on one row, with day first.

## 0.2.36

### Changed

- Calculate the initial due date from the recurrence rule instead of requiring a task date.
- Rename recurrence modes in the editor to "By calendar" and "After completion".
- Add an optional collapsible start-date boundary.
- Add yearly calendar and completion-based recurrence, including leap-day clamping.
- Keep existing tasks on their current due date unless their schedule is changed.

## 0.2.35

### Changed

- Show the first six due dates in the task editor and remove trailing punctuation from each due-date line.
- Return a configurable due-date sequence from the backend preview API instead of hardcoding individual occurrence fields.

## 0.2.34

### Changed

- Show the first three due dates in the editor without explanatory parenthetical labels and calculate both future dates through the backend scheduler.
- Allow description text areas to be resized vertically.
- Preserve file extensions when long attachment pills truncate their base names.
- Add circular Home Assistant-style hover and focus treatments to clickable icon actions.
- Use the native primary text color and hover treatment for popup close actions.

## 0.2.33

### Changed

- Reduce top and bottom whitespace inside collapsible editor and viewer boxes and match the clickable header to its visible area.
- Calculate the editor's next-due preview through the backend scheduler instead of duplicating recurrence logic in the frontend.

## 0.2.32

### Changed

- Remove history column headers and use compact natural-width date, time, and user columns so notes receive the remaining space.
- Place the next due date on a new line in the viewer. In the editor, show the entered first due date and preview the next due date if the task were completed today.
- Apply a consistent title, subtitle, and content hierarchy using Home Assistant typography and text color variables.
- Standardize action controls around the 44-pixel add-task button size and Home Assistant theme colors.
- Render due-date pills with normal font weight.

## 0.2.31

### Changed

- Use the same collapsible file and history boxes in the read-only task viewer as in the editor, without viewer delete actions.
- Show completion date, local time, user, and notes in viewer and editor history rows while keeping the editor delete action right-aligned.
- Display the human-readable recurrence summary at the end of the editor scheduling box.

### Added

- Add optional completion notes in the task viewer and persist them with the new history entry.

## 0.2.30

### Changed

- Open a new read-only task viewer when clicking a task row.
- Move task editing to a blue pencil action at the right of each row.
- Show the task title, group and assignee pills, rendered Markdown description, human-readable schedule, files, history, and completion action in the viewer.

## 0.2.29

### Fixed

- Use Home Assistant's configured local date consistently for due sensors, frontend due states, relative dates, and new-task defaults.
- Validate partial schedule updates against the complete stored task and reject incomplete fixed weekly or monthly rules.
- Fall back to the calendar anchor for legacy fixed monthly tasks without a stored day.
- Advance sliding monthly schedules from the actual completion day.
- Apply explicit due-date edits after pending history deletions so the entered date is preserved.
- Clean up files uploaded while editing when the dialog is closed without saving.
- Keep untouched weekly and monthly defaults aligned when the date of a new task changes.
- Show upload failures while preserving successfully uploaded files in the editor.
- Prevent empty task/group names and duplicate group names.
- Retry failed panel loads and refresh visible panel data periodically.
- Avoid retry failures after a partially completed set of pending file or history deletions.

### Changed

- Return signed attachment URLs in bulk instead of issuing one WebSocket request per attachment.
- Add the GitHub issue tracker to the integration manifest.
- Expand and synchronize the README and architecture documentation with current behavior.
- Add repository instructions requiring English release notes.

## 0.2.28

- Removed the entity icon from task rows.
- Task names and metadata now start at the left content edge of each row.

## 0.2.27

- Split task metadata clearly: task date and assignment share one row, while attachments use a separate row.
- Display task dates relatively and keep the exact date in a tooltip.
- Removed the recurrence-mode pill from the list.
- Standardized spacing between pills.

## 0.2.26

- Added a check-circle completion action with confirmation to every task row.
- Display attachments as individual authenticated filename links at the end of the task metadata.
- Removed the completion button from the task editor.
- Extended the confirmation dialog to support both destructive and successful actions.

## 0.2.25

- Display assigned Home Assistant users as an additional task pill.
- Hide the user pill for unassigned tasks.

## 0.2.24

- Replaced browser `confirm()` prompts for groups and tasks with a shared Home Assistant-style dialog.
- Cancel, outside click, and Escape close the prompt without deleting; destructive confirmation is highlighted in red.

## 0.2.23

- Replaced the browser group `datalist` with a custom Home Assistant-style combobox.
- Display matching existing groups in a dedicated result area.
- Display new group names as an explicit create action.
- Added search, expand, and clear icons to clarify selection state.

## 0.2.22

- Display the version in the upper-right corner.
- Moved assignment directly after scheduling and added optional active Home Assistant user selection.
- Store the assigned user on the task and expose it as an entity attribute.
- Replaced the Cancel button with a close action in the fixed editor header.

## 0.2.21

- Removed task drag and drop.
- Moved group selection into its own Assignment section.
- Marked the required Name field with a red asterisk.
- Replaced per-group add rows with one fixed global Add task button.

## 0.2.20

- Added drag and drop between groups in the list.
- Added short-hold movement on touch devices.
- Highlighted the target group and expanded it after a move.

## 0.2.19

- Regenerate the entity ID without collisions when a task changes groups.
- Preserve the stable unique ID during a move.

## 0.2.18

- Replaced the global Add group entry with Add task.
- Added group autocomplete, inline group creation, and the Tasks fallback group to the task editor.
- Allow existing tasks to change groups and move their entity to the matching virtual device.

## 0.2.17

- Assign tasks without a group to an automatically created Tasks fallback group.
- Keep the fallback group as a regular virtual Home Assistant device so task entities remain available to automations.

## 0.2.16

- Fixed the editor below the top edge so expanding sections no longer moves it vertically.

## 0.2.15

- Collapse Scheduling, Files, and History by default in the task editor.
- Added chevrons to expand and collapse those sections.

## 0.2.14 and earlier

- Added the initial Home Tasker integration, virtual group devices, due-state task entities, task history, recurrence scheduling, and task-owned uploads.
- Added the expandable group/task panel and iterated on its filters, sorting, actions, dialogs, mobile layout, and attachment presentation.
- Replaced the temporary recurrence implementation with fixed and sliding daily, weekly, and monthly schedules.
- Added registry cleanup for deleted tasks and groups and dynamic entity creation for new tasks.
