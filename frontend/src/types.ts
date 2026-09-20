export type PageStatus = 'pending' | 'in_progress' | 'success' | 'failed' | 'cancelled'

export interface Page {
  id: string
  title: string | null
  url: string
  status: PageStatus
  links_count: number
  created_at: string
}

export interface Paginated<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}
