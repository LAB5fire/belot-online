import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { useGameStore } from '../store/gameStore'

export function HomePage() {
  const navigate = useNavigate()
  const { createRoom, joinRoom, isLoading, error, clearError } = useGameStore()

  const [name, setName] = useState('')
  const [code, setCode] = useState('')
  const [mode, setMode] = useState<'menu' | 'join'>('menu')

  const handleCreate = async () => {
    if (!name.trim()) return
    clearError()
    await createRoom(name.trim())
    if (!useGameStore.getState().error) navigate('/lobby')
  }

  const handleJoin = async () => {
    if (!name.trim() || code.trim().length < 4) return
    clearError()
    await joinRoom(code.trim().toUpperCase(), name.trim())
    if (!useGameStore.getState().error) navigate('/lobby')
  }

  return (
    <div
      className="min-h-screen flex flex-col items-center justify-center text-white p-6"
      style={{ background: 'radial-gradient(ellipse at center, #1e6b3c 0%, #0a2a17 100%)' }}
    >
      <motion.div
        initial={{ y: -50, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 0.8, ease: 'easeOut' }}
        className="text-center mb-10"
      >
        <div className="flex justify-center gap-4 text-5xl mb-4">
          <span>♠</span>
          <span className="text-red-500">♥</span>
          <span className="text-red-500">♦</span>
          <span>♣</span>
        </div>
        <h1 className="text-6xl font-black tracking-tight text-yellow-300 mb-2">BELOT</h1>
        <h2 className="text-xl font-light tracking-widest text-gray-300">ONLINE · 3 PLAYERS</h2>
        <p className="mt-4 text-gray-400 max-w-md text-center text-sm">
          Bulgarian Belot for three players. Create a room, share the code with two friends,
          and play live from anywhere.
        </p>
      </motion.div>

      <AnimatePresence>
        {error && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="mb-4 bg-red-800 text-white px-4 py-2 rounded-lg text-sm"
          >
            {error}
            <button onClick={clearError} className="ml-3 underline">dismiss</button>
          </motion.div>
        )}
      </AnimatePresence>

      <motion.div
        initial={{ y: 50, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.2, duration: 0.6 }}
        className="flex flex-col gap-4 w-full max-w-xs bg-black bg-opacity-40 p-6 rounded-2xl border border-white border-opacity-10"
      >
        <label className="text-sm text-gray-300">
          Your name
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            maxLength={20}
            placeholder="e.g. Ivan"
            className="mt-1 w-full px-3 py-2 rounded-lg bg-gray-800 text-white border border-gray-600 focus:border-yellow-400 outline-none"
          />
        </label>

        {mode === 'menu' ? (
          <>
            <button
              onClick={handleCreate}
              disabled={isLoading || !name.trim()}
              className="bg-yellow-400 text-black font-black text-lg py-3 rounded-full hover:bg-yellow-300 transition-all transform hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? 'Creating...' : 'Create Room'}
            </button>
            <button
              onClick={() => setMode('join')}
              className="bg-transparent border-2 border-white text-white font-bold text-base py-2.5 rounded-full hover:bg-white hover:text-black transition-all"
            >
              Join Room
            </button>
          </>
        ) : (
          <>
            <label className="text-sm text-gray-300">
              Room code
              <input
                value={code}
                onChange={(e) => setCode(e.target.value.toUpperCase())}
                maxLength={4}
                placeholder="ABCD"
                className="mt-1 w-full px-3 py-2 rounded-lg bg-gray-800 text-white border border-gray-600 focus:border-yellow-400 outline-none tracking-[0.4em] text-center font-bold text-xl"
              />
            </label>
            <button
              onClick={handleJoin}
              disabled={isLoading || !name.trim() || code.trim().length < 4}
              className="bg-yellow-400 text-black font-black text-lg py-3 rounded-full hover:bg-yellow-300 transition-all transform hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? 'Joining...' : 'Join'}
            </button>
            <button
              onClick={() => { setMode('menu'); clearError() }}
              className="text-gray-400 text-sm hover:text-white transition-colors"
            >
              ← Back
            </button>
          </>
        )}
      </motion.div>

      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.6 }}
        className="mt-10 text-center text-gray-500 text-xs max-w-lg"
      >
        <div className="font-bold text-gray-400 mb-2">3-Player Bulgarian Belot</div>
        24-card deck (9–A) · 3 players, every player for themselves · 8 cards each ·
        8 tricks per round · First to 151 points wins
      </motion.div>
    </div>
  )
}
