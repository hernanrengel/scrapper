import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { AddPageForm } from './AddPageForm'

function jsonResponse(data: unknown, status: number) {
  return { ok: status >= 200 && status < 300, status, json: async () => data } as Response
}

describe('AddPageForm', () => {
  afterEach(() => {
    vi.restoreAllMocks()
    vi.unstubAllGlobals()
  })

  it('submits and calls onCreated on success', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(jsonResponse({}, 201)))
    const onCreated = vi.fn()

    render(
      <MemoryRouter>
        <AddPageForm onCreated={onCreated} />
      </MemoryRouter>,
    )

    await userEvent.type(screen.getByPlaceholderText('Add new page'), 'https://example.com')
    await userEvent.click(screen.getByRole('button', { name: 'Scrape' }))

    await vi.waitFor(() => expect(onCreated).toHaveBeenCalled())
  })

  it('shows the already-scraped notice with a link to the existing page on 409', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(
        jsonResponse(
          {
            existing_page: { id: 'xyz', title: 'Existing', status: 'success', links_count: 1 },
          },
          409,
        ),
      ),
    )

    render(
      <MemoryRouter>
        <AddPageForm onCreated={vi.fn()} />
      </MemoryRouter>,
    )

    await userEvent.type(screen.getByPlaceholderText('Add new page'), 'https://example.com')
    await userEvent.click(screen.getByRole('button', { name: 'Scrape' }))

    expect(await screen.findByText(/already scraped/i)).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'check it here' })).toHaveAttribute(
      'href',
      '/pages/xyz',
    )
  })

  it('shows a validation error on 400', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(jsonResponse({ url: ['Enter a valid URL.'] }, 400)),
    )

    render(
      <MemoryRouter>
        <AddPageForm onCreated={vi.fn()} />
      </MemoryRouter>,
    )

    await userEvent.type(screen.getByPlaceholderText('Add new page'), 'ftp://example.com')
    await userEvent.click(screen.getByRole('button', { name: 'Scrape' }))

    expect(await screen.findByText('Enter a valid URL.')).toBeInTheDocument()
  })
})
