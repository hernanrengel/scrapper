import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { PageListView } from './PageListView'

function jsonResponse(data: unknown, status = 200) {
  return { ok: status >= 200 && status < 300, status, json: async () => data } as Response
}

function samplePage(overrides: Record<string, unknown> = {}) {
  return {
    id: 'abc-123',
    title: 'Example Page',
    url: 'https://example.com',
    status: 'success',
    links_count: 3,
    created_at: '2026-01-01T00:00:00Z',
    ...overrides,
  }
}

function listResponse(results: unknown[], count = results.length) {
  return jsonResponse({ count, next: null, previous: null, results })
}

describe('PageListView', () => {
  afterEach(() => {
    vi.restoreAllMocks()
    vi.unstubAllGlobals()
  })

  it('renders a row with its name, status badge, and link count', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(listResponse([samplePage()])))

    render(
      <MemoryRouter>
        <PageListView />
      </MemoryRouter>,
    )

    expect(await screen.findByText('Example Page')).toBeInTheDocument()
    expect(screen.getByText('Success')).toBeInTheDocument()
    expect(screen.getByText('3')).toBeInTheDocument()
  })

  it('shows an In progress badge for a running page', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(listResponse([samplePage({ status: 'in_progress' })])),
    )

    render(
      <MemoryRouter>
        <PageListView />
      </MemoryRouter>,
    )

    expect(await screen.findByText('In progress')).toBeInTheDocument()
  })

  it('requests the clicked page number', async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(listResponse([samplePage()], 25))
    vi.stubGlobal('fetch', fetchMock)

    render(
      <MemoryRouter>
        <PageListView />
      </MemoryRouter>,
    )

    await screen.findByText('Example Page')
    await userEvent.click(screen.getByRole('button', { name: '2' }))

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining('page=2'))
    })
  })

  it('shows only Cancel for a pending row', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(listResponse([samplePage({ status: 'pending' })])),
    )

    render(
      <MemoryRouter>
        <PageListView />
      </MemoryRouter>,
    )

    await screen.findByText('Example Page')
    expect(screen.getByRole('button', { name: 'Cancel' })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Rescrape' })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Delete' })).not.toBeInTheDocument()
  })

  it('shows Rescrape and Delete, never Cancel, for a terminal-state row', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(listResponse([samplePage({ status: 'failed' })])),
    )

    render(
      <MemoryRouter>
        <PageListView />
      </MemoryRouter>,
    )

    await screen.findByText('Example Page')
    expect(screen.getByRole('button', { name: 'Rescrape' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Delete' })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Cancel' })).not.toBeInTheDocument()
  })

  it('asks for confirmation before deleting and skips the call when declined', async () => {
    const fetchMock = vi.fn().mockResolvedValue(listResponse([samplePage({ status: 'failed' })]))
    vi.stubGlobal('fetch', fetchMock)
    vi.spyOn(window, 'confirm').mockReturnValue(false)

    render(
      <MemoryRouter>
        <PageListView />
      </MemoryRouter>,
    )

    await screen.findByText('Example Page')
    await userEvent.click(screen.getByRole('button', { name: 'Delete' }))

    expect(window.confirm).toHaveBeenCalled()
    expect(fetchMock).not.toHaveBeenCalledWith(
      expect.stringContaining('/abc-123/'),
      expect.objectContaining({ method: 'DELETE' }),
    )
  })

  it('opens the insights dialog on click and renders the status history, then closes', async () => {
    const fetchMock = vi.fn((url: string) => {
      if (url.includes('/status-events/')) {
        return Promise.resolve(
          jsonResponse([
            {
              from_status: 'pending',
              to_status: 'success',
              occurred_at: '2026-01-01T00:00:01Z',
              error_message: null,
            },
          ]),
        )
      }
      return Promise.resolve(listResponse([samplePage()]))
    })
    vi.stubGlobal('fetch', fetchMock)

    render(
      <MemoryRouter>
        <PageListView />
      </MemoryRouter>,
    )

    await screen.findByText('Example Page')
    await userEvent.click(screen.getByRole('button', { name: 'Insights' }))

    expect(await screen.findByText('Pending')).toBeInTheDocument()

    await userEvent.click(screen.getByRole('button', { name: 'Close' }))
    expect(screen.queryByText('Pending')).not.toBeInTheDocument()
  })
})
