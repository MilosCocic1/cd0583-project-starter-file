import { useCallback, useState } from 'react'
import { fetchDrift, fetchHealth, fetchMetrics, fetchRuns } from './api'
import { DriftPanel } from './components/DriftPanel'
import { MetricsChart } from './components/MetricsChart'
import { RunsTable } from './components/RunsTable'
import { useNow, usePolling } from './usePolling'

function ErrorNote({ message }: { message: string | undefined }) {
  return message ? <p className="error">Couldn't refresh: {message}</p> : null
}

export default function App() {
  const [includeIdle, setIncludeIdle] = useState(false)

  const health = usePolling(fetchHealth)
  const drift = usePolling(fetchDrift)
  const metrics = usePolling(fetchMetrics)
  const loadRuns = useCallback(() => fetchRuns(includeIdle), [includeIdle])
  const runs = usePolling(loadRuns)
  const now = useNow()

  const databaseDown = health.data?.database === 'unavailable'

  return (
    <main>
      <header className="page-header">
        <div>
          <h1>Customer Attrition Risk</h1>
          <p className="subtitle">Model monitoring and automated retraining</p>
        </div>
        {health.data && (
          <span className={`badge ${databaseDown ? 'badge-critical' : 'badge-good'}`}>
            <span aria-hidden="true">{databaseDown ? '✕' : '✓'}</span>{' '}
            {databaseDown ? 'Database unavailable' : 'API and database up'}
          </span>
        )}
        {health.error && (
          <span className="badge badge-critical">
            <span aria-hidden="true">✕</span> API unreachable
          </span>
        )}
      </header>

      <ErrorNote message={drift.error} />
      {drift.data && <DriftPanel drift={drift.data} now={now} />}

      <section className="card">
        <h2>Model scores over time</h2>
        <ErrorNote message={metrics.error} />
        {metrics.data && <MetricsChart metrics={metrics.data} />}
      </section>

      <section className="card">
        <h2>Recent pipeline runs</h2>
        <ErrorNote message={runs.error} />
        {runs.data && (
          <RunsTable
            runs={runs.data}
            includeIdle={includeIdle}
            onIncludeIdleChange={setIncludeIdle}
          />
        )}
      </section>
    </main>
  )
}
