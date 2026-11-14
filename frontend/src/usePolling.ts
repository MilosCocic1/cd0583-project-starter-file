import { useCallback, useEffect, useState } from 'react'

export interface PollingState<T> {
  data: T | undefined
  error: string | undefined
  loading: boolean
}

// Calls `load` right away and then every `intervalMs`, so the dashboard
// picks up new pipeline runs without a page reload. `load` must be
// stable (wrap it in useCallback) or the polling restarts every render.
export function usePolling<T>(
  load: () => Promise<T>,
  intervalMs = 30_000,
): PollingState<T> {
  const [state, setState] = useState<PollingState<T>>({
    data: undefined,
    error: undefined,
    loading: true,
  })

  const refresh = useCallback(() => {
    load()
      .then((data) => setState({ data, error: undefined, loading: false }))
      // Keep the last good data on screen when a refresh fails.
      .catch((error: Error) =>
        setState((previous) => ({ ...previous, error: error.message, loading: false })),
      )
  }, [load])

  useEffect(() => {
    refresh()
    const timer = setInterval(refresh, intervalMs)
    return () => clearInterval(timer)
  }, [refresh, intervalMs])

  return state
}

// The current time, updated every `intervalMs`, so "x min ago" labels
// stay correct without calling Date.now() during render.
export function useNow(intervalMs = 30_000): number {
  const [now, setNow] = useState(Date.now)

  useEffect(() => {
    const timer = setInterval(() => setNow(Date.now()), intervalMs)
    return () => clearInterval(timer)
  }, [intervalMs])

  return now
}
