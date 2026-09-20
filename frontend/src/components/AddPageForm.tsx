import { useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { createPage } from '../api'
import type { PageSummary } from '../types'

type Notice = { kind: 'duplicate'; existingPage: PageSummary } | { kind: 'error'; message: string }

export function AddPageForm({ onCreated }: { onCreated: () => void }) {
  const [url, setUrl] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [notice, setNotice] = useState<Notice | null>(null)

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setSubmitting(true)
    setNotice(null)

    const result = await createPage(url)

    if (result.kind === 'created') {
      setUrl('')
      onCreated()
    } else if (result.kind === 'duplicate') {
      setNotice({ kind: 'duplicate', existingPage: result.existingPage })
    } else {
      setNotice({ kind: 'error', message: result.message })
    }

    setSubmitting(false)
  }

  return (
    <div>
      <form onSubmit={handleSubmit} className="flex gap-2">
        <input
          type="url"
          required
          placeholder="Add new page"
          value={url}
          onChange={(event) => setUrl(event.target.value)}
          className="flex-1 rounded border border-line bg-surface px-3 py-2 text-sm text-ink focus:border-accent focus:outline-none"
        />
        <button
          type="submit"
          disabled={submitting}
          className="rounded bg-accent px-4 py-2 text-sm font-medium text-accent-fg disabled:cursor-not-allowed disabled:opacity-50"
        >
          {submitting ? 'Scraping…' : 'Scrape'}
        </button>
      </form>

      {notice?.kind === 'duplicate' && (
        <p className="mt-2 text-sm text-muted">
          This URL was already scraped!{' '}
          <Link to={`/pages/${notice.existingPage.id}`} className="text-accent hover:underline">
            check it here
          </Link>
        </p>
      )}
      {notice?.kind === 'error' && (
        <p className="mt-2 text-sm text-status-failed-fg">{notice.message}</p>
      )}
    </div>
  )
}
