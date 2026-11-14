// Types and fetch helpers for the backend's read-only JSON API (backend/api.py).

export type RunStatus = 'no_new_data' | 'no_drift' | 'retrained' | 'failed'

export interface PipelineRun {
  id: number
  started_at: string
  finished_at: string
  status: RunStatus
  new_files: string | null
  deployed_score: number | null
  new_data_score: number | null
  drift_detected: boolean | null
  retrained: boolean
  new_model_score: number | null
  model_version: number | null
  error_message: string | null
}

export interface ModelScore {
  id: number
  f1_score: number
  auc_score: number | null
  dataset_source: string
  recorded_at: string
}

export interface DriftStatus {
  model_version: number
  deployed_score: number | null
  last_check: PipelineRun | null
  last_run: PipelineRun | null
}

export interface Health {
  status: string
  database: 'ok' | 'unavailable'
  model_version: number
}

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(path)
  if (!response.ok) {
    const body = await response.json().catch(() => null)
    throw new Error(body?.error ?? `${response.status} ${response.statusText}`)
  }
  return response.json() as Promise<T>
}

export const fetchHealth = () => getJson<Health>('/api/health')

export const fetchDrift = () => getJson<DriftStatus>('/api/drift')

export const fetchRuns = (includeIdle: boolean) =>
  getJson<{ runs: PipelineRun[] }>(
    `/api/runs?limit=20&include_idle=${includeIdle ? 1 : 0}`,
  ).then((body) => body.runs)

export const fetchMetrics = () =>
  getJson<{ metrics: ModelScore[] }>('/api/metrics?limit=100').then(
    (body) => body.metrics,
  )
