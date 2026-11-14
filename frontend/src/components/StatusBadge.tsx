import type { RunStatus } from '../api'
import { STATUS_DISPLAY } from '../format'

export function StatusBadge({ status }: { status: RunStatus }) {
  const { label, icon, tone } = STATUS_DISPLAY[status]
  return (
    <span className={`badge badge-${tone}`}>
      <span aria-hidden="true">{icon}</span> {label}
    </span>
  )
}
