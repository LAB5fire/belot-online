// In production set VITE_API_BASE to the backend host or URL, e.g.
// "https://belot-backend.onrender.com" or just "belot-backend.onrender.com".
// In dev it is empty and Vite proxies /api and /ws to the local backend
// (see vite.config.ts).
function normalizeBase(raw: string): string {
  if (!raw) return ''
  if (/^https?:\/\//.test(raw)) return raw.replace(/\/$/, '')
  return `https://${raw.replace(/\/$/, '')}`
}

export const API_BASE: string = normalizeBase((import.meta.env.VITE_API_BASE as string) || '')

export function httpUrl(path: string): string {
  return `${API_BASE}${path}`
}

export function wsUrl(path: string): string {
  if (API_BASE) {
    // Derive ws(s):// from the configured http(s):// backend base.
    return API_BASE.replace(/^http/, 'ws') + path
  }
  const proto = window.location.protocol === 'https:' ? 'wss' : 'ws'
  return `${proto}://${window.location.host}${path}`
}
