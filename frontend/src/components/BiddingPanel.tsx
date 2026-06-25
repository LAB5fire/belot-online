import { motion } from 'framer-motion'
import clsx from 'clsx'
import type { GameType, Bid } from '../types/game'
import { GAME_TYPE_LABELS } from '../types/game'
import { useGameStore } from '../store/gameStore'

interface BiddingPanelProps {
  availableBids: GameType[]
  currentBid: GameType | null
  bids: Bid[]
  isYourTurn: boolean
  playerNames: string[]
}

// Buttons sit on a dark background, so use light, legible colors (the old
// dark gray made ♣ Clubs and ♠ Spades invisible).
const SUIT_COLORS: Record<string, string> = {
  clubs: 'text-gray-100',
  diamonds: 'text-red-400',
  hearts: 'text-red-400',
  spades: 'text-gray-100',
  no_trump: 'text-blue-300',
  all_trump: 'text-purple-300',
}

export function BiddingPanel({ availableBids, currentBid, bids, isYourTurn, playerNames }: BiddingPanelProps) {
  const placeBid = useGameStore((s) => s.placeBid)

  const handleBid = (gt: GameType | null) => {
    if (!isYourTurn) return
    placeBid(gt)
  }

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      className="bg-black bg-opacity-80 rounded-2xl p-6 text-white w-full max-w-md mx-auto"
    >
      <h2 className="text-xl font-bold text-center mb-4 text-yellow-300">
        {isYourTurn ? 'Your Bid' : 'Waiting for players to bid…'}
      </h2>

      {bids.length > 0 && (
        <div className="mb-4">
          <div className="text-xs text-gray-400 mb-2">Bid history:</div>
          <div className="flex flex-wrap gap-2">
            {bids.map((bid, i) => (
              <div key={i} className="text-xs px-2 py-1 rounded bg-gray-800">
                <span className="text-gray-400">{playerNames[bid.player] ?? `P${bid.player + 1}`}: </span>
                <span className={bid.game_type ? SUIT_COLORS[bid.game_type] : 'text-gray-500'}>
                  {bid.game_type ? GAME_TYPE_LABELS[bid.game_type] : 'Pass'}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {currentBid && (
        <div className="text-center mb-4 text-sm text-gray-300">
          Current bid:{' '}
          <span className={clsx('font-bold', SUIT_COLORS[currentBid])}>{GAME_TYPE_LABELS[currentBid]}</span>
        </div>
      )}

      {isYourTurn && (
        <div className="space-y-3">
          <div className="grid grid-cols-3 gap-2">
            {availableBids.map((gt) => (
              <button
                key={gt}
                onClick={() => handleBid(gt)}
                className={clsx(
                  'py-3 px-2 rounded-lg font-bold text-sm transition-all',
                  'bg-gray-800 hover:bg-gray-700 border border-gray-600',
                  'hover:border-yellow-400 hover:scale-105',
                  SUIT_COLORS[gt],
                )}
              >
                {GAME_TYPE_LABELS[gt]}
              </button>
            ))}
          </div>
          <button
            onClick={() => handleBid(null)}
            className={clsx(
              'w-full py-3 rounded-lg font-bold text-gray-400',
              'bg-gray-900 hover:bg-gray-800 border border-gray-700',
              'hover:border-red-500 transition-all',
            )}
          >
            Pass
          </button>
        </div>
      )}
    </motion.div>
  )
}
