import type { DriftStatus } from '../api'
import { formatDateTime, formatScore, formatTimeAgo } from '../format'
import { StatusBadge } from './StatusBadge'

// fullprocess.py runs every 10 minutes; two missed runs means the
// scheduler is probably down.
const SCHEDULER_STALE_MINUTES = 20

interface DriftPanelProps {
  drift: DriftStatus
  now: number
}

export function DriftPanel({ drift, now }: DriftPanelProps) {
  const { last_check: check, last_run: lastRun } = drift
  const schedulerStale =
    lastRun != null &&
    now - new Date(lastRun.started_at).getTime() > SCHEDULER_STALE_MINUTES * 60_000

  return (
    <section className="tiles" aria-label="Drift status">
      <div className="tile">
        <div className="tile-label">Deployed model</div>
        <div className="tile-value">v{drift.model_version}</div>
        <div className="tile-note">
          F1 at deployment {formatScore(drift.deployed_score)}
        </div>
      </div>

      <div className="tile">
        <div className="tile-label">Last drift check</div>
        {check ? (
          <>
            <div className="tile-value">
              <StatusBadge status={check.status} />
            </div>
            <div className="tile-note">
              F1 {formatScore(check.new_data_score)} on new data vs{' '}
              {formatScore(check.deployed_score)} deployed
              <br />
              {formatDateTime(check.started_at)}
            </div>
          </>
        ) : (
          <div className="tile-note">No new data has been checked yet.</div>
        )}
      </div>

      <div className="tile">
        <div className="tile-label">Scheduler</div>
        {lastRun ? (
          <>
            <div className="tile-value">
              {schedulerStale ? (
                <span className="badge badge-critical">
                  <span aria-hidden="true">!</span> Stale
                </span>
              ) : (
                <span className="badge badge-good">
                  <span aria-hidden="true">✓</span> Running
                </span>
              )}
            </div>
            <div className="tile-note">
              Last run {formatTimeAgo(lastRun.started_at, now)}
            </div>
          </>
        ) : (
          <div className="tile-note">The pipeline hasn't run yet.</div>
        )}
      </div>
    </section>
  )
}
