export async function moveTasksToBacklog(ids: string[], apiUrl: string): Promise<void> {
  await Promise.all(ids.map(id =>
    fetch(`${apiUrl}/tasks/${id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ scheduled_date: null }),
    })
  ))
}
