import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { useGameStore } from '../store/gameStore'

export function LobbyPage() {
  const navigate = useNavigate()
  const { code, token, mySeat, room, connected, startGame, leave, restore, connect } = useGameStore()

  // Reconnect on refresh, or bounce home if there are no credentials.
  useEffect(() => {
    if (!token) {
      if (!restore()) navigate('/')
    } else {
      connect()
    }
  }, [])

  // Move everyone into the game once it starts.
  useEffect(() => {
    if (room?.status === 'playing') navigate('/game')
  }, [room?.status])

  const handleLeave = () => {
    leave()
    navigate('/')
  }

  const isHost = mySeat !== null && room?.host_seat === mySeat
  const players = room?.players ?? []
  const canStart = isHost && players.length === (room?.max_players ?? 3)

  return (
    <div
      className="min-h-screen flex flex-col items-center justify-center text-white p-6"
      style={{ background: 'radial-gradient(ellipse at center, #1e6b3c 0%, #0a2a17 100%)' }}
    >
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-black bg-opacity-50 rounded-2xl p-8 w-full max-w-md border border-white border-opacity-10"
      >
        <h1 className="text-2xl font-bold text-center text-yellow-300 mb-1">Game Lobby</h1>
        <p className="text-center text-gray-400 text-sm mb-6">
          {connected ? 'Share this code with your friends' : 'Connecting…'}
        </p>

        <div className="text-center mb-6">
          <div className="text-xs text-gray-400 uppercase tracking-wide mb-1">Room code</div>
          <div className="text-5xl font-black tracking-[0.3em] text-white bg-gray-800 rounded-xl py-3 px-4 inline-block">
            {code ?? '----'}
          </div>
        </div>

        <div className="space-y-2 mb-6">
          <div className="text-xs text-gray-400 uppercase tracking-wide">
            Players ({players.length}/{room?.max_players ?? 3})
          </div>
          {Array.from({ length: room?.max_players ?? 3 }).map((_, seat) => {
            const p = players.find((pl) => pl.seat === seat)
            return (
              <div
                key={seat}
                className={`flex items-center justify-between px-4 py-3 rounded-lg ${
                  p ? 'bg-gray-800' : 'bg-gray-900 border border-dashed border-gray-700'
                }`}
              >
                <span className={p ? 'font-semibold' : 'text-gray-500 italic'}>
                  {p ? p.name : 'Waiting for player…'}
                  {p && seat === mySeat && <span className="text-yellow-400 text-xs ml-2">(you)</span>}
                  {p && seat === room?.host_seat && <span className="text-green-400 text-xs ml-2">host</span>}
                </span>
                {p && (
                  <span className={`text-xs ${p.connected ? 'text-green-400' : 'text-gray-500'}`}>
                    {p.connected ? '● online' : '○ offline'}
                  </span>
                )}
              </div>
            )
          })}
        </div>

        {isHost ? (
          <button
            onClick={startGame}
            disabled={!canStart}
            className="w-full bg-yellow-400 text-black font-black text-lg py-3 rounded-full hover:bg-yellow-300 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {canStart ? 'Start Game' : `Waiting for ${(room?.max_players ?? 3) - players.length} more…`}
          </button>
        ) : (
          <div className="text-center text-gray-400 text-sm py-3">
            Waiting for the host to start the game…
          </div>
        )}

        <button
          onClick={handleLeave}
          className="w-full mt-3 text-gray-400 text-sm hover:text-red-300 transition-colors"
        >
          Leave room
        </button>
      </motion.div>
    </div>
  )
}
