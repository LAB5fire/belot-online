import { motion, AnimatePresence } from 'framer-motion'
import { CardComponent } from './CardComponent'
import type { TrickCard } from '../types/game'

interface TrickAreaProps {
  currentTrick: TrickCard[]
  mySeat: number
  numPlayers?: number
  lastTrickWinnerName?: string | null
}

// Position by seat RELATIVE to the viewer, so "you" are always at the bottom.
const REL_POSITIONS: Record<number, React.CSSProperties> = {
  0: { bottom: '8%', left: '50%', transform: 'translateX(-50%)' }, // you
  1: { left: '8%', top: '38%' },                                   // next (left)
  2: { right: '8%', top: '38%' },                                  // after (right)
}

export function TrickArea({ currentTrick, mySeat, numPlayers = 3, lastTrickWinnerName }: TrickAreaProps) {
  return (
    <div className="relative w-full h-full">
      <div className="absolute inset-0 flex items-center justify-center">
        <div className="w-32 h-32 rounded-full border-2 border-green-600 border-opacity-30 flex items-center justify-center">
          {lastTrickWinnerName && (
            <motion.div
              initial={{ scale: 0, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0, opacity: 0 }}
              className="text-center text-white text-xs opacity-80"
            >
              <div className="text-yellow-300 font-bold text-sm">Trick won</div>
              <div>{lastTrickWinnerName}</div>
            </motion.div>
          )}
        </div>
      </div>

      <AnimatePresence>
        {currentTrick.map(({ player, card }) => {
          const rel = ((player - mySeat) % numPlayers + numPlayers) % numPlayers
          return (
            <motion.div
              key={`${player}-${card.suit}-${card.rank}`}
              initial={{ scale: 0, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.5, opacity: 0 }}
              transition={{ type: 'spring', stiffness: 300, damping: 25 }}
              className="absolute"
              style={REL_POSITIONS[rel]}
            >
              <CardComponent card={card} small />
            </motion.div>
          )
        })}
      </AnimatePresence>
    </div>
  )
}
