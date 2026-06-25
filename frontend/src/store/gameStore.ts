import { create } from 'zustand'
import type { Card, GameType, GameState, RoomMeta } from '../types/game'
import { roomApi } from '../api/roomApi'
import { wsUrl } from '../api/config'

const STORAGE_KEY = 'belot_room'

interface SavedCreds {
  code: string
  token: string
  seat: number
}

function saveCreds(c: SavedCreds) {
  try {
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(c))
  } catch {
    /* ignore */
  }
}

function loadCreds(): SavedCreds | null {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY)
    return raw ? (JSON.parse(raw) as SavedCreds) : null
  } catch {
    return null
  }
}

function clearCreds() {
  try {
    sessionStorage.removeItem(STORAGE_KEY)
  } catch {
    /* ignore */
  }
}

let socket: WebSocket | null = null

interface GameStore {
  code: string | null
  token: string | null
  mySeat: number | null
  room: RoomMeta | null
  game: GameState | null
  connected: boolean
  error: string | null
  isLoading: boolean

  createRoom: (name: string) => Promise<void>
  joinRoom: (code: string, name: string) => Promise<void>
  connect: () => void
  restore: () => boolean
  startGame: () => void
  placeBid: (gt: GameType | null) => void
  playCard: (card: Card) => void
  leave: () => void
  clearError: () => void
}

export const useGameStore = create<GameStore>((set, get) => ({
  code: null,
  token: null,
  mySeat: null,
  room: null,
  game: null,
  connected: false,
  error: null,
  isLoading: false,

  createRoom: async (name: string) => {
    set({ isLoading: true, error: null })
    try {
      const creds = await roomApi.createRoom(name)
      saveCreds(creds)
      set({ code: creds.code, token: creds.token, mySeat: creds.seat, isLoading: false })
      get().connect()
    } catch (err) {
      set({ error: err instanceof Error ? err.message : 'Failed to create room', isLoading: false })
    }
  },

  joinRoom: async (code: string, name: string) => {
    set({ isLoading: true, error: null })
    try {
      const creds = await roomApi.joinRoom(code, name)
      saveCreds(creds)
      set({ code: creds.code, token: creds.token, mySeat: creds.seat, isLoading: false })
      get().connect()
    } catch (err) {
      set({ error: err instanceof Error ? err.message : 'Failed to join room', isLoading: false })
    }
  },

  connect: () => {
    const { code, token } = get()
    if (!code || !token) return
    if (socket && (socket.readyState === WebSocket.OPEN || socket.readyState === WebSocket.CONNECTING)) {
      return
    }

    const ws = new WebSocket(wsUrl(`/ws/${code}?token=${encodeURIComponent(token)}`))
    socket = ws

    ws.onopen = () => set({ connected: true })

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data)
        if (msg.type === 'state') {
          set({ room: msg.room as RoomMeta, game: msg.game as GameState | null })
        } else if (msg.type === 'error') {
          set({ error: msg.message })
        }
      } catch {
        /* ignore malformed */
      }
    }

    ws.onclose = () => {
      set({ connected: false })
      if (socket === ws) socket = null
    }

    ws.onerror = () => {
      set({ error: 'Connection error' })
    }
  },

  restore: () => {
    const creds = loadCreds()
    if (!creds) return false
    set({ code: creds.code, token: creds.token, mySeat: creds.seat })
    get().connect()
    return true
  },

  startGame: () => socket?.send(JSON.stringify({ action: 'start' })),

  placeBid: (gt) => socket?.send(JSON.stringify({ action: 'bid', game_type: gt })),

  playCard: (card) => socket?.send(JSON.stringify({ action: 'play', card })),

  leave: () => {
    clearCreds()
    if (socket) {
      socket.onclose = null
      socket.close()
      socket = null
    }
    set({
      code: null,
      token: null,
      mySeat: null,
      room: null,
      game: null,
      connected: false,
      error: null,
    })
  },

  clearError: () => set({ error: null }),
}))
