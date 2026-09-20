import { useEffect, useState } from 'react'
import { Link as RouterLink, useParams } from 'react-router-dom'
import { fetchLinks, fetchPage } from '../api'
import { Pagination } from '../components/Pagination'
import { StatusBadge } from '../components/StatusBadge'
import type { Link, PageDetail, Paginated } from '../types'

const PAGE_SIZE = 10

export function PageDetailView() {
  const { id } = useParams<{ id: string }>()
  const [page, setPage] = useState<PageDetail | null>(null)
  const [links, setLinks] = useState<Paginated<Link> | null>(null)
  const [linksPage, setLinksPage] = useState(1)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!id) return
    fetchPage(id)
      .then(setPage)
      .catch(() => setError('Could not load this page.'))
  }, [id])

  useEffect(() => {
    if (!id) return
    fetchLinks(id, linksPage)
      .then(setLinks)
      .catch(() => setError('Could not load this page.'))
  }, [id, linksPage])

  if (error) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-10">
        <p className="text-sm text-status-failed-fg">{error}</p>
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-3xl px-4 py-10">
      <RouterLink to="/" className="text-sm text-accent hover:underline">
        &lt; Back
      </RouterLink>

      {page && (
        <div className="mt-4 flex items-center gap-3">
          <h1 className="font-mono text-lg font-medium tracking-tight">
            {page.title ?? page.url}
          </h1>
          <StatusBadge status={page.status} />
        </div>
      )}

      {page?.error_message && (
        <p className="mt-2 text-sm text-status-failed-fg">{page.error_message}</p>
      )}

      <table className="mt-6 w-full border-collapse text-sm [&_td]:align-middle [&_th]:align-middle">
        <thead>
          <tr className="border-b border-line text-left text-muted">
            <th className="py-2 font-medium">Name</th>
            <th className="py-2 font-medium">Link</th>
          </tr>
        </thead>
        <tbody>
          {links?.results.map((link) => (
            <tr key={link.id} className="border-b border-line last:border-0">
              <td className="py-3 pr-4">{link.name_html}</td>
              <td className="py-3 font-mono text-muted">{link.href}</td>
            </tr>
          ))}
          {links && links.results.length === 0 && (
            <tr>
              <td colSpan={2} className="py-8 text-center text-muted">
                No links found on this page.
              </td>
            </tr>
          )}
        </tbody>
      </table>

      {links && (
        <div className="mt-6">
          <Pagination
            page={linksPage}
            count={links.count}
            pageSize={PAGE_SIZE}
            onPageChange={setLinksPage}
          />
        </div>
      )}
    </div>
  )
}
