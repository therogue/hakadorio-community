import { describe, it, expect, vi, beforeEach } from 'vitest'
import { moveTasksToBacklog, getMoveToBacklogLabel } from './taskApi'

const API_URL = 'http://localhost:8000'

beforeEach(() => {
  vi.restoreAllMocks()
})

describe('getMoveToBacklogLabel', () => {
  it('returns "Move to Backlog" for a single task', () => {
    expect(getMoveToBacklogLabel(1)).toBe('Move to Backlog')
  })

  it('returns "Move all to Backlog" for multiple tasks', () => {
    expect(getMoveToBacklogLabel(2)).toBe('Move all to Backlog')
    expect(getMoveToBacklogLabel(10)).toBe('Move all to Backlog')
  })
})

describe('moveTasksToBacklog', () => {
  it('sends PATCH with scheduled_date=null for each id', async () => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: true })
    vi.stubGlobal('fetch', fetchMock)

    await moveTasksToBacklog(['id-1', 'id-2'], API_URL)

    expect(fetchMock).toHaveBeenCalledTimes(2)
    expect(fetchMock).toHaveBeenCalledWith(`${API_URL}/tasks/id-1`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ scheduled_date: null }),
    })
    expect(fetchMock).toHaveBeenCalledWith(`${API_URL}/tasks/id-2`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ scheduled_date: null }),
    })
  })

  it('makes all requests in parallel (Promise.all)', async () => {
    const order: string[] = []
    const fetchMock = vi.fn().mockImplementation((url: string) => {
      order.push(url)
      return Promise.resolve({ ok: true })
    })
    vi.stubGlobal('fetch', fetchMock)

    await moveTasksToBacklog(['id-a', 'id-b', 'id-c'], API_URL)

    expect(fetchMock).toHaveBeenCalledTimes(3)
  })

  it('resolves with empty array when no ids provided', async () => {
    const fetchMock = vi.fn()
    vi.stubGlobal('fetch', fetchMock)

    await moveTasksToBacklog([], API_URL)

    expect(fetchMock).not.toHaveBeenCalled()
  })

  it('throws when the server returns a non-ok response', async () => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: false, status: 404 })
    vi.stubGlobal('fetch', fetchMock)

    await expect(moveTasksToBacklog(['id-1'], API_URL)).rejects.toThrow('404')
  })
})
