import { httpUrl } from './config'

export interface RoomCredentials {
  code: string
  token: string
  seat: number
}

async function postJson<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(httpUrl(path), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) {
    let detail = 'Request failed'
    try {
      const data = await res.json()
      detail = data.detail || detail
    } catch {
      /* ignore */
    }
    throw new Error(detail)
  }
  return res.json()
}

export const roomApi = {
  createRoom: (name: string) =>
    postJson<RoomCredentials>('/api/rooms', { name }),

  joinRoom: (code: string, name: string) =>
    postJson<RoomCredentials>(`/api/rooms/${code.toUpperCase()}/join`, { name }),
}
