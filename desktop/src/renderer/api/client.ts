export async function fetchApi(path: string, options?: RequestInit) {
  const r = await fetch(`http://127.0.0.1:8765${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!r.ok) throw new Error(r.statusText)
  if (r.status === 204) return null
  return r.json()
}
