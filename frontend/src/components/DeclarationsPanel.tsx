import { motion } from 'framer-motion'
import type { Declaration } from '../types/game'
import { CardComponent } from './CardComponent'

interface DeclarationsPanelProps {
  declarations: Record<string, Declaration[]>
  winningPlayer: number | null
  playerNames: string[]
}

const DECL_TYPE_LABELS: Record<string, string> = {
  tierce: 'Tierce (3 in row)',
  quart: 'Quart (4 in row)',
  quint: 'Quint (5+ in row)',
  four_jacks: '4 Jacks',
  four_nines: '4 Nines',
  four_aces: '4 Aces',
  four_tens: '4 Tens',
  four_kings: '4 Kings',
  four_queens: '4 Queens',
  belot: 'Belot (K+Q)',
}

export function DeclarationsPanel({ declarations, winningPlayer, playerNames }: DeclarationsPanelProps) {
  const hasDeclarations = Object.values(declarations).some((d) => d.length > 0)
  if (!hasDeclarations) return null

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-black bg-opacity-85 rounded-2xl p-5 text-white w-full max-w-2xl mx-auto"
    >
      <h2 className="text-lg font-bold text-center mb-3 text-yellow-300">Declarations</h2>
      {winningPlayer !== null && (
        <div className="text-center mb-4 text-sm">
          <span className="font-bold text-green-400">
            {playerNames[winningPlayer] ?? `Player ${winningPlayer + 1}`}
          </span>{' '}
          wins declarations!
        </div>
      )}

      <div className="grid grid-cols-3 gap-3">
        {([0, 1, 2] as const).map((playerIdx) => {
          const playerDecls = declarations[String(playerIdx)] || []
          if (playerDecls.length === 0) return null
          const isWinner = playerIdx === winningPlayer
          return (
            <div
              key={playerIdx}
              className={`rounded-lg p-3 ${
                isWinner ? 'bg-green-900 bg-opacity-50 border border-green-600' : 'bg-gray-800 opacity-70'
              }`}
            >
              <div className="font-bold mb-2 text-sm truncate">
                {playerNames[playerIdx] ?? `Player ${playerIdx + 1}`}
              </div>
              {playerDecls.map((decl, i) => (
                <div key={i} className="text-xs mb-2">
                  <div className="flex justify-between">
                    <span className="text-gray-300">{DECL_TYPE_LABELS[decl.type] || decl.type}</span>
                    <span className="text-yellow-400 font-bold">+{decl.points}</span>
                  </div>
                  <div className="flex gap-1 mt-1">
                    {decl.cards.slice(0, 5).map((card, ci) => (
                      <CardComponent key={ci} card={card} small />
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )
        })}
      </div>
    </motion.div>
  )
}
