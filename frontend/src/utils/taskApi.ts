export function getMoveToBacklogLabel(count: number): string {
  return count > 1 ? 'Move all to Backlog' : 'Move to Backlog'
}

export async function moveTasksToBacklog(ids: string[], apiUrl: string): Promise<void> {
  await Promise.all(ids.map(async id => {
    const res = await fetch(`${apiUrl}/tasks/${id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ scheduled_date: null }),
    })
    if (!res.ok) throw new Error(String(res.status))
  }))
}
