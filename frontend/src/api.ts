import type { Link, Page, PageDetail, PageSummary, Paginated, StatusEvent } from './types'

const API_BASE = '/api/v1'

async function request<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`)
  if (!response.ok) {
    throw new Error(`Request to ${path} failed with status ${response.status}`)
  }
  return response.json() as Promise<T>
}

export function fetchPages(page: number): Promise<Paginated<Page>> {
  return request(`/pages/?page=${page}`)
}

export function fetchPage(id: string): Promise<PageDetail> {
  return request(`/pages/${id}/`)
}

export function fetchLinks(id: string, page: number): Promise<Paginated<Link>> {
  return request(`/pages/${id}/links/?page=${page}`)
}

export function fetchStatusEvents(id: string): Promise<StatusEvent[]> {
  return request(`/pages/${id}/status-events/`)
}

export type CreatePageResult =
  | { kind: 'created' }
  | { kind: 'duplicate'; existingPage: PageSummary }
  | { kind: 'invalid'; message: string }
  | { kind: 'error'; message: string }

export async function createPage(url: string): Promise<CreatePageResult> {
  let response: Response
  try {
    response = await fetch(`${API_BASE}/pages/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url }),
    })
  } catch {
    return { kind: 'error', message: 'Could not reach the server. Try again.' }
  }

  const data = await response.json().catch(() => null)

  if (response.status === 201) return { kind: 'created' }
  if (response.status === 409) return { kind: 'duplicate', existingPage: data.existing_page }
  if (response.status === 400) {
    return { kind: 'invalid', message: data?.url?.[0] ?? 'That URL is not valid.' }
  }
  return { kind: 'error', message: 'Something went wrong. Try again.' }
}
