import type { LucideIcon } from 'lucide-react'

export function IconButton({
  icon: Icon,
  label,
  onClick,
  variant = 'default',
}: {
  icon: LucideIcon
  label: string
  onClick: () => void
  variant?: 'default' | 'danger'
}) {
  const color =
    variant === 'danger' ? 'text-status-failed-fg hover:bg-status-failed' : 'text-muted hover:bg-status-pending hover:text-ink'

  return (
    <button
      type="button"
      onClick={onClick}
      title={label}
      aria-label={label}
      className={`inline-flex h-7 w-7 items-center justify-center rounded-full ${color}`}
    >
      <Icon size={16} strokeWidth={2} />
    </button>
  )
}
