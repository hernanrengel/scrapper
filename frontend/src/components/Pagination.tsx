const WINDOW = 2

function pageNumbers(current: number, total: number): (number | 'gap')[] {
  const pages = new Set<number>([1, total, current])
  for (let offset = 1; offset <= WINDOW; offset++) {
    if (current - offset >= 1) pages.add(current - offset)
    if (current + offset <= total) pages.add(current + offset)
  }
  const sorted = [...pages].sort((a, b) => a - b)

  const withGaps: (number | 'gap')[] = []
  sorted.forEach((n, i) => {
    if (i > 0 && n - sorted[i - 1] > 1) withGaps.push('gap')
    withGaps.push(n)
  })
  return withGaps
}

export function Pagination({
  page,
  count,
  pageSize,
  onPageChange,
}: {
  page: number
  count: number
  pageSize: number
  onPageChange: (page: number) => void
}) {
  const totalPages = Math.max(1, Math.ceil(count / pageSize))
  if (totalPages <= 1) return null

  const buttonClass = (active: boolean) =>
    `min-w-8 rounded border px-2 py-1 text-sm ${
      active
        ? 'border-accent bg-accent text-accent-fg'
        : 'border-line bg-surface text-ink hover:border-accent'
    }`

  return (
    <nav className="flex items-center justify-center gap-1.5" aria-label="Pagination">
      <button
        type="button"
        className={`${buttonClass(false)} disabled:cursor-not-allowed disabled:opacity-40`}
        disabled={page <= 1}
        onClick={() => onPageChange(page - 1)}
      >
        Previous
      </button>
      {pageNumbers(page, totalPages).map((n, i) =>
        n === 'gap' ? (
          <span key={`gap-${i}`} className="px-1 text-sm text-muted">
            …
          </span>
        ) : (
          <button
            key={n}
            type="button"
            className={buttonClass(n === page)}
            aria-current={n === page ? 'page' : undefined}
            onClick={() => onPageChange(n)}
          >
            {n}
          </button>
        ),
      )}
      <button
        type="button"
        className={`${buttonClass(false)} disabled:cursor-not-allowed disabled:opacity-40`}
        disabled={page >= totalPages}
        onClick={() => onPageChange(page + 1)}
      >
        Next
      </button>
    </nav>
  )
}
