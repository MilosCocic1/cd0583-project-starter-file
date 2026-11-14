import type { PipelineRun } from '../api'
import { formatDateTime, formatScore } from '../format'
import { StatusBadge } from './StatusBadge'

interface RunsTableProps {
  runs: PipelineRun[]
  includeIdle: boolean
  onIncludeIdleChange: (includeIdle: boolean) => void
}

export function RunsTable({ runs, includeIdle, onIncludeIdleChange }: RunsTableProps) {
  return (
    <>
      <div className="filters">
        <label>
          <input
            type="checkbox"
            checked={includeIdle}
            onChange={(e) => onIncludeIdleChange(e.target.checked)}
          />{' '}
          Show runs with no new data
        </label>
      </div>

      {runs.length === 0 ? (
        <p className="empty">No pipeline runs recorded yet.</p>
      ) : (
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th className="num">Run</th>
                <th>Started</th>
                <th>Status</th>
                <th>New files</th>
                <th className="num">Deployed F1</th>
                <th className="num">F1 on new data</th>
                <th className="num">Model</th>
                <th className="num">Retrained F1</th>
              </tr>
            </thead>
            <tbody>
              {runs.map((run) => (
                <tr key={run.id}>
                  <td className="num">#{run.id}</td>
                  <td>{formatDateTime(run.started_at)}</td>
                  <td title={run.error_message ?? undefined}>
                    <StatusBadge status={run.status} />
                  </td>
                  <td>{run.new_files?.split(',').join(', ') ?? '—'}</td>
                  <td className="num">{formatScore(run.deployed_score)}</td>
                  <td className="num">{formatScore(run.new_data_score)}</td>
                  <td className="num">
                    {run.model_version == null ? '—' : `v${run.model_version}`}
                  </td>
                  <td className="num">{formatScore(run.new_model_score)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  )
}
