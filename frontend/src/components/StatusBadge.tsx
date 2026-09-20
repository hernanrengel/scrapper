import type { PageStatus } from '../types'

const STYLES: Record<PageStatus, { bg: string; fg: string; label: string; pulse?: boolean }> = {
  pending: { bg: 'bg-status-pending', fg: 'text-status-pending-fg', label: 'Pending' },
  in_progress: {
    bg: 'bg-status-progress',
    fg: 'text-status-progress-fg',
    label: 'In progress',
    pulse: true,
  },
  success: { bg: 'bg-status-success', fg: 'text-status-success-fg', label: 'Success' },
  failed: { bg: 'bg-status-failed', fg: 'text-status-failed-fg', label: 'Failed' },
  cancelled: { bg: 'bg-status-cancelled', fg: 'text-status-cancelled-fg', label: 'Cancelled' },
}

export function StatusBadge({ status }: { status: PageStatus }) {
  const { bg, fg, label, pulse } = STYLES[status]

  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium ${bg} ${fg}`}>
      <span className={`h-1.5 w-1.5 rounded-full ${fg.replace('text-', 'bg-')} ${pulse ? 'status-dot-pulse' : ''}`} />
      {label}
    </span>
  )
}
