import { motion, AnimatePresence } from 'framer-motion'
import clsx from 'clsx'
import { CardComponent, CardBack } from './CardComponent'
import type { Card, GamePhase } from '../types/game'

interface PlayerHandProps {
  position: 'bottom' | 'left' | 'right'
  isYou: boolean
  hand: Card[] | number
  isCurrentPlayer: boolean
  isDealer?: boolean
  legalMoves?: Card[]
  selectedCard?: Card | null
  onCardClick?: (card: Card) => void
  yourTurn?: boolean
  gamePhase: GamePhase
  label: string
}

function cardKey(c: Card) {
  return `${c.suit}-${c.rank}`
}

export function PlayerHand({
  position,
  isYou,
  hand,
  isCurrentPlayer,
  isDealer = false,
  legalMoves = [],
  selectedCard,
  onCardClick,
  yourTurn = false,
  gamePhase,
  label,
}: PlayerHandProps) {
  const cardCount = typeof hand === 'number' ? hand : hand.length
  const cards = typeof hand === 'number' ? null : hand

  const isPlayable = (card: Card) =>
    isYou &&
    yourTurn &&
    gamePhase === 'playing' &&
    legalMoves.some((lm) => lm.suit === card.suit && lm.rank === card.rank)

  const isSelected = (card: Card) =>
    selectedCard?.suit === card.suit && selectedCard?.rank === card.rank

  const isSide = position === 'left' || position === 'right'

  const containerClass = clsx(
    'flex items-center justify-center relative',
    'flex-row',
  )

  const labelClass = clsx(
    'text-white text-sm font-semibold px-2 py-1 rounded-full absolute z-10 whitespace-nowrap',
    isCurrentPlayer ? 'bg-yellow-500 text-black' : 'bg-black bg-opacity-50',
    position === 'bottom' && '-top-8 left-1/2 -translate-x-1/2',
    position === 'left' && '-top-8 left-1/2 -translate-x-1/2',
    position === 'right' && '-top-8 left-1/2 -translate-x-1/2',
  )

  return (
    <div className={clsx('relative', position === 'bottom' ? 'py-2' : 'py-4')}>
      <div className={labelClass}>
        {label}
        {isDealer && <span className="ml-1 text-xs" title="Dealer">🂠</span>}
        {isCurrentPlayer && <span className="ml-1 animate-pulse">●</span>}
      </div>

      {/* Other players: face-down card backs */}
      {!isYou && (
        <div className={containerClass}>
          {Array.from({ length: cardCount }).map((_, i) => (
            <CardBack key={i} small={isSide} className="-mx-2" />
          ))}
        </div>
      )}

      {/* Your hand: face-up cards */}
      {isYou && cards && (
        <div className={containerClass}>
          <AnimatePresence>
            {cards.map((card, i) => {
              const playable = isPlayable(card)
              const selected = isSelected(card)
              return (
                <motion.div
                  key={cardKey(card)}
                  initial={{ y: 60, opacity: 0 }}
                  animate={{ y: 0, opacity: 1 }}
                  exit={{ y: 60, opacity: 0, scale: 0.8 }}
                  transition={{ delay: i * 0.05, duration: 0.3 }}
                  className={clsx('-mx-1', selected && '-translate-y-4')}
                >
                  <CardComponent
                    card={card}
                    playable={playable}
                    selected={selected}
                    onClick={() => playable && onCardClick?.(card)}
                  />
                </motion.div>
              )
            })}
          </AnimatePresence>
        </div>
      )}
    </div>
  )
}
