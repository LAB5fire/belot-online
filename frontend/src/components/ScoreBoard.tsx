import { motion, AnimatePresence } from 'framer-motion'
import clsx from 'clsx'
import type { GameState } from '../types/game'
import { GAME_TYPE_LABELS } from '../types/game'

interface ScoreBoardProps {
  gameState: GameState
  playerNames: string[]
  mySeat: number
}

const TARGET = 151
const BAR_COLORS = ['bg-blue-500', 'bg-emerald-500', 'bg-rose-500']

export function ScoreBoard({ gameState, playerNames, mySeat }: ScoreBoardProps) {
  const { cumulative_scores, tricks_won_count, game_type, last_round, round_number, num_players } = gameState
  const n = num_players ?? 3

  return (
    <div className="bg-black bg-opacity-70 rounded-xl p-4 text-white text-sm min-w-48">
      <div className="text-yellow-300 font-bold text-center mb-3 text-base">
        Round {round_number}
        {game_type && (
          <div className="text-gray-300 text-xs font-normal mt-1">{GAME_TYPE_LABELS[game_type]}</div>
        )}
      </div>

      <div className="space-y-2 mb-3">
        {Array.from({ length: n }).map((_, seat) => {
          const score = cumulative_scores[String(seat)] ?? 0
          const tricks = tricks_won_count[String(seat)] ?? 0
          return (
            <div key={seat} className="px-3 py-2 rounded-lg bg-gray-800 bg-opacity-60">
              <div className="flex justify-between items-center">
                <div className="font-bold truncate max-w-[7rem]">
                  {playerNames[seat] ?? `Player ${seat + 1}`}
                  {seat === mySeat && <span className="text-yellow-400 text-xs ml-1">(you)</span>}
                </div>
                <div className="text-xl font-bold">{score}</div>
              </div>
              <div className="flex justify-between items-center mt-1">
                <div className="h-1.5 bg-gray-700 rounded-full overflow-hidden flex-1 mr-2">
                  <div
                    className={clsx('h-full transition-all duration-500', BAR_COLORS[seat % BAR_COLORS.length])}
                    style={{ width: `${Math.min(100, (score / TARGET) * 100)}%` }}
                  />
                </div>
                <div className="text-xs text-gray-400">{tricks}t</div>
              </div>
            </div>
          )
        })}
      </div>

      <div className="text-xs text-gray-400 text-center mb-2">First to {TARGET} wins</div>

      <AnimatePresence>
        {last_round && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="border-t border-gray-700 pt-2 text-xs text-gray-400"
          >
            <div className="text-center font-bold text-gray-300 mb-1">Last Round</div>
            {last_round.inside && last_round.inside_caller !== null && (
              <div className="text-center text-red-400 font-bold mb-1">
                ВЪТРЕ! {playerNames[last_round.inside_caller] ?? `Player ${last_round.inside_caller + 1}`} got caught
                {last_round.beater !== null && (
                  <> — {playerNames[last_round.beater] ?? `Player ${last_round.beater + 1}`} takes the points</>
                )}
              </div>
            )}
            {last_round.hanging && last_round.inside_caller !== null && (
              <div className="text-center text-orange-300 font-bold mb-1">
                ВИСЯЩИ! {playerNames[last_round.inside_caller] ?? `Player ${last_round.inside_caller + 1}`} tied —
                {' '}{last_round.hanging_amount} pts carry to next round
              </div>
            )}
            {last_round.valat !== null && last_round.valat !== undefined && (
              <div className="text-center text-yellow-400 font-bold mb-1">
                VALAT! ({playerNames[last_round.valat] ?? `Player ${last_round.valat + 1}`})
              </div>
            )}
            {Array.from({ length: n }).map((_, seat) => (
              <div key={seat} className="flex justify-between">
                <span className="truncate max-w-[7rem]">{playerNames[seat] ?? `Player ${seat + 1}`}</span>
                <span>+{last_round.final_scores[String(seat)] ?? 0}</span>
              </div>
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
