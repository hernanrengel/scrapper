import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { fetchPages } from '../api'
import { AddPageForm } from '../components/AddPageForm'
import { InsightsDialog } from '../components/InsightsDialog'
import { Pagination } from '../components/Pagination'
import { StatusBadge } from '../components/StatusBadge'
import type { Page, Paginated } from '../types'

const PAGE_SIZE = 10
const POLL_INTERVAL_MS = 3000

export function PageListView() {
  const [page, setPage] = useState(1)
  const [data, setData] = useState<Paginated<Page> | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [insightsPageId, setInsightsPageId] = useState<string | null>(null)

  const load = useCallback(async (targetPage: number) => {
    try {
      const result = await fetchPages(targetPage)
      setData(result)
      setError(null)
    } catch {
      setError('Could not load pages. Retrying…')
    }
  }, [])

  useEffect(() => {
    // oxlint-disable-next-line react/set-state-in-effect -- fetching on mount/page-change is the documented React pattern, not an accidental cascade
    load(page)
    const interval = setInterval(() => load(page), POLL_INTERVAL_MS)
    return () => clearInterval(interval)
  }, [page, load])

  function handleCreated() {
    setPage(1)
    load(1)
  }

  return (
    <div className="mx-auto max-w-3xl px-4 py-10">
      <h1 className="font-mono text-lg font-medium tracking-tight">Web Scrapper</h1>

      <div className="mt-6">
        <AddPageForm onCreated={handleCreated} />
      </div>

      {error && <p className="mt-4 text-sm text-status-failed-fg">{error}</p>}

      <table className="mt-6 w-full border-collapse text-sm [&_td]:align-middle [&_th]:align-middle">
        <thead>
          <tr className="border-b border-line text-left text-muted">
            <th className="py-2 font-medium">Name</th>
            <th className="py-2 font-medium">Status</th>
            <th className="py-2 text-right font-medium">Total links</th>
            <th className="py-2 pr-0 text-right font-medium">Actions</th>
          </tr>
        </thead>
        <tbody>
          {data?.results.map((p) => (
            <tr key={p.id} className="border-b border-line last:border-0">
              <td className="py-3 pr-4">
                <Link to={`/pages/${p.id}`} className="text-accent hover:underline">
                  {p.title ?? p.url}
                </Link>
              </td>
              <td className="py-3">
                <StatusBadge status={p.status} />
              </td>
              <td className="py-3 text-right font-mono">{p.links_count}</td>
              <td className="py-3 pl-4 text-right">
                <button
                  type="button"
                  onClick={() => setInsightsPageId(p.id)}
                  className="text-sm text-accent hover:underline"
                >
                  Insights
                </button>
              </td>
            </tr>
          ))}
          {data && data.results.length === 0 && (
            <tr>
              <td colSpan={4} className="py-8 text-center text-muted">
                No pages scraped yet.
              </td>
            </tr>
          )}
        </tbody>
      </table>

      {data && (
        <div className="mt-6">
          <Pagination page={page} count={data.count} pageSize={PAGE_SIZE} onPageChange={setPage} />
        </div>
      )}

      {insightsPageId && (
        <InsightsDialog pageId={insightsPageId} onClose={() => setInsightsPageId(null)} />
      )}
    </div>
  )
}
