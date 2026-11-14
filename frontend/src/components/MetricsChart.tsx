import { useMemo, useState } from 'react'
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import type { ModelScore } from '../api'
import { formatDateTime, formatScore } from '../format'

const SERIES = [
  { key: 'f1_score', name: 'F1', color: 'var(--series-1)' },
  { key: 'auc_score', name: 'AUC', color: 'var(--series-2)' },
] as const

const SOURCE_LABELS: Record<string, string> = {
  testdata: 'Test set',
  ingesteddata: 'New data (drift checks)',
}

interface EndLabelProps {
  x?: number | string
  y?: number | string
  index?: number
  value?: unknown
}

// Direct label on the last point of a line only, never on every point.
function endLabel(name: string, lastIndex: number) {
  return function EndLabel({ x, y, index, value }: EndLabelProps) {
    if (index !== lastIndex || typeof value !== 'number' || x == null || y == null) {
      return null
    }
    return (
      <text x={Number(x) + 8} y={Number(y)} dy={4} className="end-label">
        {name} {formatScore(value)}
      </text>
    )
  }
}

export function MetricsChart({ metrics }: { metrics: ModelScore[] }) {
  const sources = useMemo(
    () => [...new Set(metrics.map((m) => m.dataset_source))],
    [metrics],
  )
  const [chosenSource, setChosenSource] = useState('testdata')
  const source = sources.includes(chosenSource) ? chosenSource : sources[0]
  const rows = metrics.filter((m) => m.dataset_source === source)

  if (rows.length === 0) {
    return <p className="empty">No model scores recorded yet.</p>
  }

  return (
    <>
      <div className="filters">
        <label>
          Scored on{' '}
          <select value={source} onChange={(e) => setChosenSource(e.target.value)}>
            {sources.map((s) => (
              <option key={s} value={s}>
                {SOURCE_LABELS[s] ?? s}
              </option>
            ))}
          </select>
        </label>
      </div>

      <div className="chart">
        <ResponsiveContainer width="100%" height={280}>
          <LineChart data={rows} margin={{ top: 8, right: 72, bottom: 0, left: -16 }}>
            <CartesianGrid vertical={false} stroke="var(--grid)" />
            <XAxis
              dataKey="recorded_at"
              tickFormatter={(iso: string) => new Date(iso).toLocaleDateString()}
              stroke="var(--axis)"
              tick={{ fill: 'var(--text-muted)', fontSize: 12 }}
              minTickGap={32}
            />
            <YAxis
              domain={[0, 1]}
              ticks={[0, 0.25, 0.5, 0.75, 1]}
              stroke="var(--axis)"
              tick={{ fill: 'var(--text-muted)', fontSize: 12 }}
            />
            <Tooltip
              labelFormatter={(iso) => formatDateTime(String(iso))}
              formatter={(value) => formatScore(value as number | null)}
              contentStyle={{
                background: 'var(--surface)',
                border: '1px solid var(--border)',
                borderRadius: 8,
                color: 'var(--text-primary)',
              }}
              cursor={{ stroke: 'var(--axis)' }}
            />
            <Legend
              iconType="plainline"
              itemSorter={null}
              formatter={(value) => <span className="legend-label">{value}</span>}
            />
            {SERIES.map((s) => (
              <Line
                key={s.key}
                dataKey={s.key}
                name={s.name}
                stroke={s.color}
                strokeWidth={2}
                dot={{ r: 4, fill: s.color, stroke: 'var(--surface)', strokeWidth: 2 }}
                activeDot={{ r: 6, stroke: 'var(--surface)', strokeWidth: 2 }}
                label={endLabel(s.name, rows.length - 1)}
                isAnimationActive={false}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>

      <details className="table-view">
        <summary>Show as table</summary>
        <table>
          <thead>
            <tr>
              <th>Recorded</th>
              <th className="num">F1</th>
              <th className="num">AUC</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((m) => (
              <tr key={m.id}>
                <td>{formatDateTime(m.recorded_at)}</td>
                <td className="num">{formatScore(m.f1_score)}</td>
                <td className="num">{formatScore(m.auc_score)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </details>
    </>
  )
}
