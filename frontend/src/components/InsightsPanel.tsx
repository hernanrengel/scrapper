import { StatusBadge } from './StatusBadge'
import type { StatusEvent } from '../types'

export function InsightsPanel({ events }: { events: StatusEvent[] }) {
  if (events.length === 0) {
    return <p className="text-sm text-muted">No status history yet.</p>
  }

  return (
    <ol className="space-y-3 border-l border-line pl-4">
      {events.map((event) => (
        <li key={event.occurred_at}>
          <div className="flex items-center gap-2 text-sm">
            {event.from_status && (
              <>
                <StatusBadge status={event.from_status} />
                <span className="text-muted">→</span>
              </>
            )}
            <StatusBadge status={event.to_status} />
            <span className="text-xs text-muted">
              {new Date(event.occurred_at).toLocaleString()}
            </span>
          </div>
          {event.error_message && (
            <p className="mt-1 text-sm text-status-failed-fg">{event.error_message}</p>
          )}
        </li>
      ))}
    </ol>
  )
}
