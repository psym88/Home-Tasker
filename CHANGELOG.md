# Changelog

All release notes and changelog entries are written in English.

## 0.2.100

### Changed

- Record `NFC Tag` in completion notes when a task is completed by scanning its assigned tag.
- Share the viewer's compact pill typography, spacing and icon alignment with grouped task rows.

## 0.2.99

### Changed

- Place the NFC tag pill after the assignee in grouped task rows.
- Add compact icons to assignee and attachment pills and use one shared icon size across all pills.

## 0.2.98

### Changed

- Load available tag IDs and entity-registry names from Home Assistant for a native task-editor selection.
- Show the assigned tag name as a small pill beside tasks in the grouped list and in the task viewer.

## 0.2.97

### Added

- Allow a unique Home Assistant NFC tag ID to be assigned to each task.
- Complete matching tasks from native `tag_scanned` events, including recurrence advancement, history attribution and live entity/calendar refreshes.

## 0.2.96

### Fixed

- Restrict orphan task-entity cleanup to the binary-sensor domain so task mutations no longer remove the Home Tasker calendar from the entity registry.

## 0.2.95

### Fixed

- Represent expanded task repetitions as independent calendar events with a unique task-and-date ID.
- Remove misleading recurrence IDs from already flattened events so Home Assistant does not interpret the refreshed list as a native recurring series.

## 0.2.94

### Fixed

- Remove the duplicate direct calendar-listener refresh after task mutations and rely on Home Assistant's state-driven debounced calendar update.
- Keep the calendar feed available when an older task contains incomplete recurrence data by limiting the failure to that task's future projection.

## 0.2.93

### Fixed

- Keep calendar state and subscription refreshes on the Home Assistant event loop when task mutations dispatch an update.
- Prevent thread-safety errors from `async_write_ha_state` after creating, editing, completing or deleting a task.

## 0.2.92

### Changed

- Expand each task's future repetitions across the calendar's requested date range instead of showing only the current due date.
- Identify individual occurrences by date while retaining the task ID as the stable calendar series ID.
- Project after-completion schedules from each displayed due date until a real completion recalculates the series.

## 0.2.91

### Added

- Add a read-only Home Assistant calendar named Home Tasker with one all-day event for every task's current due date.
- Synchronize calendar events immediately when tasks are created, edited, completed or deleted, including event descriptions, group locations and stable task IDs.

## 0.2.90

### Changed

- Consolidate config-flow and frontend translations into the integration-level `translations/en.json` and `translations/de.json` catalogs.
- Move the English frontend fallback out of JavaScript and load it from `en.json` before overlaying the selected language.
- Serve the shared translation directory through its own static integration URL and remove the duplicate frontend translation directory.

## 0.2.89

### Added

- Add complete runtime localization for the sidebar panel, dashboard card, card editor, viewers, editors, confirmations, action menus, schedules and errors.
- Add German frontend translations with English fallback and Home Assistant locale-aware dates, times, weekdays, months, sorting and relative due dates.

### Changed

- Remove embedded German UI copy from frontend source and use stable translation keys throughout.

## 0.2.88

### Changed

- Consolidate viewer, editor and task-list typography into four reusable Home Assistant-themed classes.
- Remove field-specific typography selectors, runtime style injection and typographic inline overrides without changing the rendered hierarchy.

## 0.2.87

### Changed

- Keep task viewer pills on Home Assistant's small font size while retaining normal secondary typography.
- Use secondary text colors for empty file and history states and for task titles in the sidebar task list.

## 0.2.86

### Changed

- Standardize task viewer and editor labels on Home Assistant's medium primary typography.
- Render planning and assignment labels with normal primary typography and form, preview and history content with normal secondary typography.

## 0.2.85

### Changed

- Render task descriptions with Home Assistant's native Markdown component and remove the custom Markdown parser and redundant viewer styles.

## 0.2.84

### Fixed

- Recalculate the due date from the remaining completion history when entries are removed in any order.
- Rebuild each remaining history entry's due-date transition so subsequent deletions continue to restore the correct schedule.

## 0.2.83

### Changed

- Allow every authenticated Home Assistant user to perform group mutations while keeping the sidebar panel administrator-only.
- Return a signed attachment URL directly from uploads and remove the redundant attachment-signing WebSocket request.
- Consolidate shared recurrence validation schemas and remove obsolete administrator and dialog helper code.

## 0.2.82

### Changed

- Make dashboard edit-mode controls available to every authenticated Home Assistant user, with visibility controlled solely by the card configuration.
- Allow authenticated users to create, edit and delete tasks, preview schedules, manage task attachments and remove task history entries while keeping dedicated group administration protected.

## 0.2.81

### Changed

- Rewrite the README as a concise, user-focused installation and usage guide.
- Add an official My Home Assistant button for adding Home Tasker as a custom HACS integration repository.

## 0.2.80

### Fixed

- Keep the current due-date preview visible while schedule changes are recalculated, preventing transient text and layout flicker.

## 0.2.79

### Changed

- Replace the browser-specific planning interval spinner with a theme-aware minus/value/plus stepper.
- Match the interval stepper and frequency dropdown at a consistent 44-pixel height while retaining direct numeric and arrow-key input.

## 0.2.78

### Fixed

- Preserve individual dashboard task-tile borders when the outer card background and frame are hidden.
- Add a theme-aware outer border around every grouped task-list block.

## 0.2.77

### Changed

- Restore a compact standard sorting dropdown in the task list and style it consistently with the themed planning selects.
- Keep dashboard task tile surfaces neutral while retaining status colors exclusively on due-date text.

## 0.2.76

### Changed

- Replace the task-list sorting HTML dropdown with Home Assistant's native `ha-select` and `ha-list-item` components.
- Give dashboard task rows theme-aware, tile-like status fills and hover colors while retaining the overdue, today, and future distinctions.

## 0.2.75

### Changed

- Open attachments from task lists, viewers, and editors in a native Home Assistant adaptive dialog instead of a new browser page.
- Preview images, audio, video, PDFs, and other browser-supported inline files while retaining an explicit download action.

## 0.2.74

### Changed

- Center the plus icon and add-task label consistently in the dashboard card, above the panel group list, and inside expanded groups.

## 0.2.73

### Changed

- Replace the task panel's fixed bottom-right add button with a full-width muted dashed placeholder above the group list.
- Add a matching final placeholder to every expanded group and preselect that group when creating a task from it.
- Remove the now-unused floating-add styles.

## 0.2.72

### Changed

- Render the dashboard add-task action as a full-width muted placeholder row with a dashed border above the tasks.

### Fixed

- Suppress Home Assistant's card border variables and force the outer background, border, and shadow off when the frameless option is enabled.

## 0.2.71

### Changed

- Always sort dashboard-card tasks from oldest to newest and remove the sorting-direction option from the visual editor.
- Add a dashboard-local option to hide the card's outer background, border, and shadow while retaining the separate task elements.

### Fixed

- Add a registration regression guard confirming that the dashboard card uses guarded global custom-element definitions without a Browser Mod dependency.

## 0.2.70

### Changed

- Remove unreachable legacy overlay containers, modal headers, editor actions, and related CSS after the migration to native Home Assistant dialogs.
- Render the native editor footer directly and isolate editor-only form styles from panel and dashboard roots.
- Keep only collapsible-section rules in the shared dialog layout mixin.

## 0.2.69

### Changed

- Remove task and group delete icons from editor dialogs now that deletion is available in each row's overflow menu.
- Restore the neutral secondary color for vertical-dots action icons.

### Fixed

- Keep the extension directly beside short attachment base names while retaining base-name-only truncation for long filenames.

## 0.2.68

### Fixed

- Use the composed event path for overflow-menu outside-click detection so Shadow DOM retargeting no longer removes the menu before Edit or Delete can run.

## 0.2.67

### Changed

- Replace task and group pencil actions with accessible vertical-dots overflow menus in the panel and dashboard card.
- Offer edit and confirmed delete actions directly from each menu, with neutral edit hover styling and a red destructive hover treatment.

## 0.2.66

### Changed

- Move task and group editor save actions into Home Assistant's native adaptive-dialog footer, matching the task viewer and keeping the primary action visible while content scrolls.

## 0.2.65

### Fixed

- Truncate long attachment base names consistently in task viewers and editors while preserving the file extension.
- Reserve right-aligned columns for attachment sizes and editor delete actions so long names cannot widen or horizontally scroll dialogs.

## 0.2.64

### Fixed

- Include the shared collapsible layout rules in native task and group form dialogs so sections and chevrons render and toggle correctly.

## 0.2.63

### Changed

- Host task and group editors and all Home Tasker confirmations in registered Home Assistant adaptive dialogs opened through `show-dialog`.
- Place the dashboard card's add-task action above the task elements so it remains immediately accessible for long lists.

## 0.2.62

### Changed

- Open the complete task viewer through Home Assistant's native `show-dialog` contract and `ha-adaptive-dialog`, including native header, responsive dialog sizing, footer action, and nested confirmation dialog.

## 0.2.61

### Fixed

- Use the neutral secondary action color for dashboard task pencil icons.
- Restore the shared horizontal sticky dialog header and collapsible-section layout when viewers and editors are opened from the dashboard card.

## 0.2.60

### Changed

- Render dashboard tasks as separated rounded elements and color their due dates orange for today, red when overdue, and green when upcoming.

### Fixed

- Preserve card-editor focus and open dropdowns by avoiding full rerenders on routine Home Assistant state updates.

## 0.2.59

### Fixed

- Make the dashboard card and sidebar panel inherit from a shared unregistered base class so scoped custom-element registries such as Browser Mod can construct the card.

## 0.2.58

### Added

- Add an automatically registered Home Tasker dashboard card with flat due-date rows, view and edit modes, a visual editor, due/group/assignee filters, and configurable sort direction.

### Changed

- Allow authenticated Home Assistant users to view and complete tasks while keeping structural edits and history changes administrator-only.

## 0.2.57

### Changed

- Use Home Assistant's small font-size variable for all pills.

## 0.2.56

### Changed

- Use Home Assistant's secondary text color for task and group pencil actions and the global expand/collapse control.

## 0.2.55

### Changed

- Swap the resting group-header and task-row background colors while preserving the existing task-row hover tint.

## 0.2.54

### Changed

- Match Home Assistant data tables: darker non-hovering group headers, transparent task rows on the table background, and a subtle row-only hover tint.

## 0.2.53

### Changed

- Give group headers a subtle Home Assistant neutral background and matching hover fill so they remain visually distinct from transparent task rows.

## 0.2.52

### Fixed

- Give task rows an explicitly transparent resting background while retaining the original neutral row hover, restoring clear pill and icon feedback.
- Restore the original neutral Home Assistant hover treatment for icon actions.

## 0.2.51

### Fixed

- Keep icon-action hover feedback visible inside hovered task-list rows in light themes by using Home Assistant's quiet primary hover fill.
- Use Home Assistant's lighter quiet neutral fill for task-row hover so it remains distinct from pill backgrounds.

## 0.2.50

### Changed

- Split the Home Tasker panel into focused ES modules for state, lists, editors, viewers, dialogs, shared helpers, and styles.
- Expose reusable due-date task sorting as a foundation for a future flat dashboard card.

### Tests

- Add focused frontend tests for due-date sorting, stable input handling, and grouped task rendering.

## 0.2.48

### Fixed

- Refresh each task's problem sensor exactly at local midnight so the due state (and any automations bound to it) flips at the date rollover without waiting for a mutation or a poll.

### Changed

- Turn off entity polling and rely on push updates, matching the integration's `local_push` class.
- Use Home Assistant's `dt` utility for date and timestamp calculations so due dates follow the configured Home Assistant time zone.

### Removed

- Drop the unused single-file `attachment/sign` WebSocket command; the panel signs attachments through `attachment/sign_all` and the initial list response.

## 0.2.47

### Fixed

- Keep the currently scheduled calendar occurrence when a task is completed before its due date.
- Continue advancing calendar tasks normally when completed on time and skip missed occurrences only when completed late.

## 0.2.46

### Changed

- Reduce group-row padding to match task rows.
- Replace the open-task pill with a circular red count badge.
- Replace source-text typography assertions with a behavioral completion test that verifies the next due date is persisted.

## 0.2.45

### Fixed

- Calculate due-date column widths across the complete preview table so every date starts at the same horizontal position.

## 0.2.44

### Changed

- Display the due-date preview in normal Home Assistant body size and primary text color.
- Align weekdays and dates in a responsive two-column layout.
- Add spacing between the recurrence description and the due-date table.

## 0.2.43

### Changed

- Match the optional start-date heading to the other planning subtitles in size, weight, and color.
- Place the start-date selection action below its heading with tighter vertical spacing.
- Present the start-date removal action in the Home Assistant error color.

## 0.2.42

### Changed

- Standardize labels, pills, history entries, and planning controls on Home Assistant body typography.
- Reserve the small Home Assistant font size for the compact due-date preview list.
- Make group names larger than task names in the main task list and render task names at normal weight.

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
