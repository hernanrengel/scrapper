import type { Page, Paginated } from './types'

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
