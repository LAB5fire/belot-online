import { motion } from 'framer-motion'
import clsx from 'clsx'
import type { Card, Suit } from '../types/game'
import { SUIT_SYMBOLS, SUIT_COLORS } from '../types/game'

interface CardComponentProps {
  card?: Card
  faceDown?: boolean
  selected?: boolean
  playable?: boolean
  small?: boolean
  onClick?: () => void
  animate?: boolean
  className?: string
}

const RANK_DISPLAY: Record<string, string> = {
  '7': '7', '8': '8', '9': '9', '10': '10',
  J: 'J', Q: 'Q', K: 'K', A: 'A',
}

export function CardComponent({
  card,
  faceDown = false,
  selected = false,
  playable = false,
  small = false,
  onClick,
  animate = false,
  className,
}: CardComponentProps) {
  if (faceDown || !card) {
    return (
      <motion.div
        initial={animate ? { y: -60, opacity: 0 } : undefined}
        animate={animate ? { y: 0, opacity: 1 } : undefined}
        className={clsx(
          'relative rounded-lg border-2 border-gray-400 bg-gradient-to-br from-blue-800 to-blue-950',
          'shadow-card select-none',
          small ? 'w-10 h-14' : 'w-16 h-24',
          className,
        )}
      >
        <div className="absolute inset-1 rounded border border-blue-600 opacity-40" />
        <div className="absolute inset-0 flex items-center justify-center text-blue-400 opacity-30">
          <span className={small ? 'text-lg' : 'text-2xl'}>✦</span>
        </div>
      </motion.div>
    )
  }

  const color = SUIT_COLORS[card.suit]
  const symbol = SUIT_SYMBOLS[card.suit]
  const rank = RANK_DISPLAY[card.rank]

  return (
    <motion.div
      initial={animate ? { y: -60, opacity: 0, rotateY: 180 } : undefined}
      animate={animate ? { y: 0, opacity: 1, rotateY: 0 } : undefined}
      whileHover={playable ? { y: -12, scale: 1.05 } : undefined}
      transition={{ type: 'spring', stiffness: 300, damping: 20 }}
      onClick={playable ? onClick : undefined}
      className={clsx(
        'relative rounded-lg border-2 bg-white shadow-card select-none',
        'flex flex-col justify-between p-1',
        small ? 'w-10 h-14' : 'w-16 h-24',
        selected && 'border-yellow-400 shadow-card-selected -translate-y-3',
        !selected && 'border-amber-200',
        playable && 'cursor-pointer hover:border-yellow-300 hover:shadow-card-hover',
        !playable && onClick && 'cursor-default',
        className,
      )}
      style={{ color }}
    >
      <div className={clsx('font-bold leading-none', small ? 'text-xs' : 'text-sm')}>
        <div>{rank}</div>
        <div className={small ? 'text-xs' : 'text-sm'}>{symbol}</div>
      </div>
      <div
        className={clsx(
          'absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 font-bold opacity-20',
          small ? 'text-2xl' : 'text-4xl',
        )}
      >
        {symbol}
      </div>
      <div
        className={clsx(
          'font-bold leading-none self-end rotate-180',
          small ? 'text-xs' : 'text-sm',
        )}
      >
        <div>{rank}</div>
        <div className={small ? 'text-xs' : 'text-sm'}>{symbol}</div>
      </div>
    </motion.div>
  )
}

export function CardBack({ small = false, className = '' }) {
  return (
    <div
      className={clsx(
        'rounded-lg border-2 border-gray-400 bg-gradient-to-br from-blue-800 to-blue-950',
        'shadow-card',
        small ? 'w-10 h-14' : 'w-16 h-24',
        className,
      )}
    />
  )
}
