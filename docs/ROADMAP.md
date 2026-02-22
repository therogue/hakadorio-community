## 0.1

- Use SQLAlchemy ORM instead of raw SQL for database modeling
- Auto-schedule unscheduled tasks based on priority, duration, and availability
- Backlog tab for parking unscheduled tasks separately from the day view
- LLM-assigned priority scoring (0-4) for new tasks
- Multiple chat threads with separate conversation histories
- Bulk-complete selected tasks via multi-select
- Add Tskr logo

## 0.2
- User intent prompt: detect whether the user wants a task operation, is answering an LLM clarification, or is requesting a reschedule
- Bulk and drag-and-drop rescheduling for tasks
- User-configurable defaults: default category, priority, and conflict resolution behavior (e.g. move conflicting tasks to unscheduled or backlog)
- Design overhaul:
  - Collapsible/minimizable conversation panel
  - Spotlight-style quick-entry popup for task creation
- Intelligence hardening:
  - Prevent duplicate task creation
  - Ensure all tasks have estimated duration and priority
  - Enrich LLM context window with task metadata relevant to the current view

## 0.3
- Export all tasks to an ICS calendar file