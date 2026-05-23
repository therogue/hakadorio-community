import { describe, it, expect, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import App from '../App'
import { setupFetchMock, getFetchMock } from '../test/mocks/server'
import { DAY_SUMMARY_EXISTING } from '../test/fixtures/tasks'

function postCallsTo(path: string): unknown[] {
  const fetchMock = getFetchMock()
  return fetchMock.mock.calls.filter(([url, init]) => {
    return typeof url === 'string' && url.includes(path) && init?.method === 'POST'
  })
}

function getCallsTo(path: string): unknown[] {
  const fetchMock = getFetchMock()
  return fetchMock.mock.calls.filter(([url, init]) => {
    return typeof url === 'string' && url.includes(path) && (!init || !init.method || init.method === 'GET')
  })
}

describe('App shell', () => {
  beforeEach(() => {
    setupFetchMock()
  })

  it('renders the header with logo text', async () => {
    render(<App />)
    expect(screen.getByText('Hakadorio')).toBeInTheDocument()
  })

  it('renders the settings button', async () => {
    render(<App />)
    expect(screen.getByRole('button', { name: /settings/i })).toBeInTheDocument()
  })

  it('opens SettingsModal when settings button is clicked', async () => {
    const user = userEvent.setup()
    render(<App />)
    await user.click(screen.getByRole('button', { name: /settings/i }))
    // SettingsModal has a conflict resolution section
    await waitFor(() => {
      expect(screen.getByText(/allow overlap/i)).toBeInTheDocument()
    })
  })

  it('opens QuickEntry on Ctrl+. keydown', async () => {
    render(<App />)
    await userEvent.keyboard('{Control>}.{/Control}')
    await waitFor(() => {
      expect(screen.getByPlaceholderText(/create a task/i)).toBeInTheDocument()
    })
  })

  it('closes QuickEntry on Escape', async () => {
    render(<App />)
    await userEvent.keyboard('{Control>}.{/Control}')
    await waitFor(() => {
      expect(screen.getByPlaceholderText(/create a task/i)).toBeInTheDocument()
    })
    await userEvent.keyboard('{Escape}')
    await waitFor(() => {
      expect(screen.queryByPlaceholderText(/create a task/i)).not.toBeInTheDocument()
    })
  })

  it('renders app with structural classes present', async () => {
    const { container } = render(<App />)
    expect(container.querySelector('.app')).toBeInTheDocument()
    expect(container.querySelector('.header')).toBeInTheDocument()
    expect(container.querySelector('.main')).toBeInTheDocument()
  })
})

describe('App day-summary trigger', () => {
  beforeEach(() => {
    setupFetchMock()
  })

  it('fires POST /day-summary when day view is active for today', async () => {
    render(<App />)
    await waitFor(() => {
      expect(postCallsTo('/day-summary').length).toBeGreaterThanOrEqual(1)
    })
  })

  it('switches active conversation when /day-summary returns created=true', async () => {
    render(<App />)
    await waitFor(() => {
      expect(getCallsTo('/conversations/42').length).toBeGreaterThanOrEqual(1)
    })
  })

  it('does NOT switch active conversation when /day-summary returns created=false (AC10)', async () => {
    setupFetchMock([
      {
        match: (u) => u.includes('/day-summary'),
        handler: (_u, init) => {
          if (init?.method === 'POST') {
            return new Response(JSON.stringify(DAY_SUMMARY_EXISTING), {
              status: 200,
              headers: { 'Content-Type': 'application/json' },
            })
          }
          return new Response(JSON.stringify({}), { status: 405 })
        },
      },
    ])

    render(<App />)
    await waitFor(() => {
      expect(postCallsTo('/day-summary').length).toBeGreaterThanOrEqual(1)
    })
    await new Promise((r) => setTimeout(r, 50))
    expect(getCallsTo('/conversations/99').length).toBe(0)
  })

  it('does NOT POST /day-summary when day view date is not today (AC11)', async () => {
    const { container } = render(<App />)
    await waitFor(() => {
      expect(postCallsTo('/day-summary').length).toBeGreaterThanOrEqual(1)
    })
    const initialCount = postCallsTo('/day-summary').length

    const datePicker = container.querySelector('input[type="date"]') as HTMLInputElement
    expect(datePicker).not.toBeNull()
    fireEvent.change(datePicker, { target: { value: '2026-04-30' } })

    await new Promise((r) => setTimeout(r, 50))

    expect(postCallsTo('/day-summary').length).toBe(initialCount)
  })
})
