# Cognitive Load Tracking

## Problem
Users have no way to gauge the mental effort required by their scheduled tasks. A day packed with high-effort tasks leads to burnout, but the calendar only shows time — not cognitive cost.

## Solution
Add a `cognitive_load` field (1–10 scale) to tasks. Multiply load by duration (in 15-min blocks) to get cognitive points. Track and display total cognitive points for a day/period.

### Scale guidelines
- 1–3: Routine/mechanical (email, filing, standup)
- 4–6: Moderate focus (code review, writing, planning)
- 7–8: High concentration (complex debugging, architecture decisions)
- 9–10: Rare/extreme (crisis management, high-stakes presentations)

Most users should rarely exceed 7–8. A score of 9+ indicates a stressful situation.

### Cognitive points formula
```
cognitive_points = cognitive_load × ceil(duration_minutes / 15)
```
Example: 1-hour task with load 3 → 3 × 4 = 12 points.

## Backend Changes

### `models.py`
- Add `cognitive_load: Optional[int] = None` to `Task` (1–10, nullable)
- Add `cognitive_load: Optional[int] = None` to `TaskUpdate`

### Alembic migration
- `ALTER TABLE tasks ADD COLUMN cognitive_load INTEGER`

### `prompts.py`
- Instruct Claude to estimate cognitive load (1–10) when creating tasks
- Add `"cognitive_load"` to the JSON response format

### `main.py`
- Parse `cognitive_load` from LLM response
- Pass through to `create_task_db` and `update_task_db`

### Metrics
- Calculate daily cognitive points: sum of `cognitive_load × ceil(duration / 15)` for all tasks on a given date
- Display location deferred to stats display feature

## Frontend Changes

### `TaskList.tsx`
- Display cognitive load indicator on each task (e.g., small badge or icon intensity)
- Add `cognitive_load` to Task interface

## Decisions
- User can specify cognitive load at creation time; if not specified, LLM estimates it
- User can override cognitive load after task is created (via edit/PATCH)
- No threshold warnings — users interpret cognitive load subjectively
- Display location for daily cognitive total deferred to stats display feature

## Open Questions
- None currently
