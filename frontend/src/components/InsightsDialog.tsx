import { useEffect, useRef, useState } from 'react'
import { fetchStatusEvents } from '../api'
import { InsightsPanel } from './InsightsPanel'
import type { StatusEvent } from '../types'

export function InsightsDialog({ pageId, onClose }: { pageId: string; onClose: () => void }) {
  const dialogRef = useRef<HTMLDialogElement>(null)
  const [events, setEvents] = useState<StatusEvent[] | null>(null)

  useEffect(() => {
    dialogRef.current?.showModal()
  }, [])

  useEffect(() => {
    // oxlint-disable-next-line react/set-state-in-effect -- fetching on pageId change is the documented React pattern, not an accidental cascade
    setEvents(null)
    fetchStatusEvents(pageId)
      .then(setEvents)
      .catch(() => setEvents([]))
  }, [pageId])

  return (
    <dialog
      ref={dialogRef}
      onClose={onClose}
      className="fixed top-1/2 left-1/2 m-0 w-full max-w-md -translate-x-1/2 -translate-y-1/2 rounded border border-line bg-surface p-6 text-ink backdrop:bg-ink/40"
    >
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-medium text-muted">Insights</h2>
        <button
          type="button"
          onClick={() => dialogRef.current?.close()}
          className="text-sm text-muted hover:text-ink"
        >
          Close
        </button>
      </div>
      <div className="mt-4">
        {events === null ? (
          <p className="text-sm text-muted">Loading…</p>
        ) : (
          <InsightsPanel events={events} />
        )}
      </div>
    </dialog>
  )
}
