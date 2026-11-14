import type { RunStatus } from './api'

export const formatScore = (score: number | null | undefined) =>
  score == null ? '—' : score.toFixed(3)

export const formatDateTime = (iso: string) =>
  new Date(iso).toLocaleString(undefined, {
    dateStyle: 'medium',
    timeStyle: 'short',
  })

export function formatTimeAgo(iso: string, now: number) {
  const minutes = Math.round((now - new Date(iso).getTime()) / 60_000)
  if (minutes < 1) return 'just now'
  if (minutes < 60) return `${minutes} min ago`
  const hours = Math.round(minutes / 60)
  if (hours < 48) return `${hours} h ago`
  return `${Math.round(hours / 24)} days ago`
}

// Every status is shown with an icon and a label, never color alone.
export const STATUS_DISPLAY: Record<RunStatus, { label: string; icon: string; tone: string }> = {
  no_new_data: { label: 'No new data', icon: '○', tone: 'neutral' },
  no_drift: { label: 'No drift', icon: '✓', tone: 'good' },
  retrained: { label: 'Retrained', icon: '↻', tone: 'warning' },
  failed: { label: 'Failed', icon: '✕', tone: 'critical' },
}
