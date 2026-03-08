# Task Timer & Progress Tracking

## Problem
Users schedule tasks with estimated durations but have no way to track actual time spent. There's no visual feedback during task execution, and no data for future time-spent reports.

## Solution
Show an inline progress bar based on `duration_minutes`. Log actual time spent for reporting. Timer auto-starts for now (future: user setting for auto vs. manual start).

### Key rules
- Timer auto-starts at the task's scheduled time (default behavior)
- Timer auto-stops when duration is reached OR when another task starts
- User can manually pause/resume a running timer
- Start button shown in UI but disabled for now (future: user setting to enable manual start)
- Progress bar = elapsed time / duration_minutes, displayed inline in task row
- Tasks under 15 minutes are treated as minimum 5 minutes for calendar display purposes
- Actual time is logged for reports (future feature)

### Minimum duration rule
Any task, regardless of how small, occupies at least 5 minutes on the calendar. This applies to:
- Visual calendar block sizing
- Cognitive load calculations (ceil(5/15) = 1 block minimum)
- Does NOT change the stored `duration_minutes` — the 5-min floor is applied at display/calculation time

## Backend Changes

### `models.py`
- Add `actual_start: Optional[str] = None` — ISO datetime when timer started
- Add `actual_end: Optional[str] = None` — ISO datetime when timer stopped
- Add these to `TaskUpdate` as well

### Alembic migration
- `ALTER TABLE tasks ADD COLUMN actual_start TEXT`
- `ALTER TABLE tasks ADD COLUMN actual_end TEXT`

### `main.py` / `database.py`
- Support updating `actual_start` and `actual_end` via PATCH
- Compute `actual_duration_minutes` as a derived property or in responses

### Future: reporting endpoint
- Aggregate actual vs. estimated durations per task/category/period
- Not in scope for initial implementation

## Frontend Changes

### `TaskList.tsx`
- Add progress bar component to each task row
- Progress = `(now - scheduled_start) / duration_minutes`
- States: not started (empty), in progress (filling), complete (full)

### Timer logic
- Poll or use `setInterval` to update progress bars every ~30 seconds
- Auto-start: compare current time to `scheduled_date` (which includes time component)
- Auto-stop: when duration is reached, or when the next scheduled task starts
- Pause/resume: user can manually pause and resume a running timer
- When progress reaches 100%, auto-stop and mark visually (but don't auto-complete the task)

### Start button
- Render a start/play button on each task row, but **disabled** for initial release
- Future: user setting to switch between auto-start and manual-start modes

### `App.css`
- Progress bar styles: background track, fill color
- Smooth animation for fill transitions

### Calendar display
- Tasks with `duration_minutes < 5` render as 5-minute blocks
- This is display-only — does not modify stored data

## Implementation Order
1. Backend: add `actual_start`, `actual_end` fields + migration
2. Frontend: progress bar component (visual only, based on scheduled time + duration)
3. Frontend: auto-start timer logic
4. Backend: log `actual_start`/`actual_end` when timer starts/stops
5. Future: reporting endpoints

## Decisions
- Timer auto-stops on duration complete or when another task starts
- No overrun state — timer stops cleanly, no need for overflow handling
- Progress bar is inline in the task row
- Manual pause/resume supported now
- Start button rendered but disabled; future user setting for auto vs. manual start

## Open Questions
- None currently
