# Home Tasker

Home Tasker is a local Home Assistant custom integration for recurring household tasks.

## Features

- Expandable group/task list in a bundled admin panel
- One virtual Home Assistant device per group
- One due-state problem `binary_sensor` per task
- Fixed calendar schedules or sliding completion-based schedules
- Daily intervals, weekly intervals with multiple weekdays, and monthly intervals with a calendar day
- Task completion history with undo by deleting a history entry
- Task-owned file uploads via browse or drag and drop

## Installation

Add this repository to HACS as a custom integration repository, install **Home Tasker**, restart Home Assistant, and add the integration under **Settings → Devices & services**.

All data and uploaded files stay inside the Home Assistant configuration directory.
