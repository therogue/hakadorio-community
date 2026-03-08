# Impact Field & Prioritization

## Problem
Users lack a way to express the benefit/value of completing a task. Priority scoring currently uses a single 0–4 scale assigned by the LLM, which doesn't account for user-perceived value.

## Solution
Add an `impact` field (1–10 scale) — a flat value per task, independent of duration or cognitive load. Use the computed score to inform LLM priority estimates and task ordering.

### Impact scale
- 1–3: Low impact (nice-to-have, minor improvement)
- 4–6: Moderate impact (meaningful progress, solid value)
- 7–8: High impact (significant outcome, key deliverable)
- 9–10: Critical impact (make-or-break, major milestone)

### Prioritization formula
Keep the existing `priority` field (0–4). Compute a ranking score to inform priority estimates and ordering:

```
priority_score = impact / (cognitive_load × duration_minutes)
```

Higher score = better return on investment (high impact, low effort).

### Sorting & scheduling
- **Display order**: auto-sort tasks by priority score (default). User can manually reorder.
- **Auto-scheduling**: when placing tasks in time slots, higher-score tasks get earlier/better slots.

## Backend Changes

### `models.py`
- Add `impact: Optional[int] = None` to `Task` (1–10, nullable)
- Add `impact: Optional[int] = None` to `TaskUpdate`

### Alembic migration
- `ALTER TABLE tasks ADD COLUMN impact INTEGER`

### `prompts.py`
- Instruct Claude to estimate impact (1–10) when creating tasks
- Add `"impact"` to JSON response format
- Include priority score in scheduling context so LLM can use it for slot selection

### `main.py`
- Parse `impact` from LLM response
- Pass through to `create_task_db` and `update_task_db`

### `scheduling.py`
- Compute priority score for each task: `impact / (cognitive_load × duration_minutes)`
- Sort tasks by score when building schedule context
- Present higher-score tasks first so LLM schedules them in preferred slots
- Handle nulls: tasks missing any of the three fields get a default score or are sorted last

## Frontend Changes

### `TaskList.tsx`
- Display impact indicator on each task
- Add `impact` to Task interface
- Default sort by priority score; user can manually reorder

## Dependencies
- Requires cognitive load feature to be implemented first (or simultaneously)

## Decisions
- Keep existing `priority` field (0–4) alongside `impact`
- Computed score informs LLM priority estimates but does not replace the priority field
- Auto-sort by priority score is the default display order
- Auto-scheduling uses priority score to assign better time slots to higher-value tasks

## Open Questions
- None currently
