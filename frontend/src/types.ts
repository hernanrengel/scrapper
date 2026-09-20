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

export interface PageSummary {
  id: string
  title: string | null
  status: PageStatus
  links_count: number
}

export interface PageDetail {
  id: string
  url: string
  title: string | null
  status: PageStatus
  error_message: string | null
  started_at: string | null
  finished_at: string | null
  created_at: string
}

export interface Link {
  id: string
  href: string
  name_html: string
}

export interface StatusEvent {
  from_status: PageStatus | null
  to_status: PageStatus
  occurred_at: string
  error_message: string | null
}
