/**
 * Calls the backend /health endpoint (proxied by Vite) and measures round-trip time.
 * Resolves to { app, status, database, latency } or throws if the backend is unreachable.
 */
export async function getHealth() {
  const start = performance.now()
  const res = await fetch('/health')
  if (!res.ok) throw new Error('Health check failed')
  const data = await res.json()
  return { ...data, latency: Math.round(performance.now() - start) }
}
