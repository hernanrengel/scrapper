import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { PageDetailView } from './PageDetailView'

function jsonResponse(data: unknown) {
  return { ok: true, status: 200, json: async () => data } as Response
}

function stubFetch(linkResults: unknown[]) {
  return vi.fn((url: string) => {
    if (url.includes('/links/')) {
      return Promise.resolve(
        jsonResponse({ count: linkResults.length, next: null, previous: null, results: linkResults }),
      )
    }
    return Promise.resolve(
      jsonResponse({
        id: 'p1',
        url: 'https://example.com',
        title: 'Example',
        status: 'success',
        error_message: null,
        started_at: null,
        finished_at: null,
        created_at: '2026-01-01T00:00:00Z',
      }),
    )
  })
}

function renderDetail() {
  render(
    <MemoryRouter initialEntries={['/pages/p1']}>
      <Routes>
        <Route path="/pages/:id" element={<PageDetailView />} />
      </Routes>
    </MemoryRouter>,
  )
}

describe('PageDetailView', () => {
  afterEach(() => {
    vi.restoreAllMocks()
    vi.unstubAllGlobals()
  })

  it('renders the links table for the given page id', async () => {
    vi.stubGlobal(
      'fetch',
      stubFetch([{ id: 'l1', href: 'https://example.com/a', name_html: 'A link' }]),
    )

    renderDetail()

    expect(await screen.findByText('A link')).toBeInTheDocument()
    expect(screen.getByText('https://example.com/a')).toBeInTheDocument()
    expect(screen.getByText('Example')).toBeInTheDocument()
  })

  it('renders link name_html as plain text, never as markup', async () => {
    vi.stubGlobal(
      'fetch',
      stubFetch([
        { id: 'l1', href: 'https://example.com/a', name_html: '<img src=x onerror=alert(1)>' },
      ]),
    )

    renderDetail()

    const cell = await screen.findByText('<img src=x onerror=alert(1)>')
    expect(cell.children.length).toBe(0)
  })
})
