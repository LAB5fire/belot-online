import { useState, useEffect, useRef, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { PlayerHand } from '../components/PlayerHand'
import { TrickArea } from '../components/TrickArea'
import { BiddingPanel } from '../components/BiddingPanel'
import { ScoreBoard } from '../components/ScoreBoard'
import { DeclarationsPanel } from '../components/DeclarationsPanel'
import { GameLog, buildLogEntry } from '../components/GameLog'
import { useGameStore } from '../store/gameStore'
import type { Card, TrickCard } from '../types/game'
import { SUIT_SYMBOLS, GAME_TYPE_LABELS } from '../types/game'

export function GamePage() {
  const navigate = useNavigate()
  const { room, game, mySeat, token, error, restore, connect, leave, playCard, clearError } = useGameStore()

  const [selectedCard, setSelectedCard] = useState<Card | null>(null)
  const [logEntries, setLogEntries] = useState<ReturnType<typeof buildLogEntry>[]>([])
  const [showDeclarations, setShowDeclarations] = useState(false)
  // Briefly hold a completed trick so the 3rd card is visible before it clears.
  const [heldTrick, setHeldTrick] = useState<TrickCard[] | null>(null)
  const prevTrickRef = useRef<TrickCard[]>([])
  const prevRoundRef = useRef<number>(0)

  const addLog = useCallback((type: 'play' | 'trick' | 'bid' | 'system', msg: string) => {
    setLogEntries((prev) => [...prev.slice(-50), buildLogEntry(type, msg)])
  }, [])

  // Reconnect on refresh, or bounce home if there is nothing to show.
  useEffect(() => {
    if (!token) {
      if (!restore()) navigate('/')
    } else {
      connect()
    }
  }, [])

  useEffect(() => {
    if (room && room.status === 'lobby') navigate('/lobby')
  }, [room?.status])

  // Show declarations briefly at the start of each round's play.
  useEffect(() => {
    if (!game) return
    if (game.round_number !== prevRoundRef.current) {
      prevRoundRef.current = game.round_number
      setLogEntries([])
    }
    if (game.phase === 'playing' && Object.keys(game.declarations).length > 0) {
      const anyDecl = Object.values(game.declarations).some((d) => d.length > 0)
      if (anyDecl) {
        setShowDeclarations(true)
        const t = setTimeout(() => setShowDeclarations(false), 4000)
        return () => clearTimeout(t)
      }
    }
  }, [game?.round_number, game?.phase])

  // Hold a completed trick on screen for a moment.
  useEffect(() => {
    if (!game) return
    const prev = prevTrickRef.current
    if (prev.length === (game.num_players ?? 3) && game.current_trick.length === 0) {
      setHeldTrick(prev)
      const t = setTimeout(() => setHeldTrick(null), 1300)
      prevTrickRef.current = game.current_trick
      return () => clearTimeout(t)
    }
    prevTrickRef.current = game.current_trick
  }, [game?.current_trick])

  if (!game || mySeat === null || !room) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ background: '#0f3d25' }}>
        <div className="text-white text-xl animate-pulse">Loading game…</div>
      </div>
    )
  }

  const n = game.num_players ?? 3
  const names: string[] = []
  room.players.forEach((p) => { names[p.seat] = p.name })
  for (let i = 0; i < n; i++) if (!names[i]) names[i] = `Player ${i + 1}`

  const leftSeat = (mySeat + 1) % n
  const rightSeat = (mySeat + 2) % n

  const yourTurn = game.phase === 'playing' && game.current_player === mySeat
  const isYourBidTurn = game.phase === 'bidding' && game.current_player === mySeat
  const legalMoves: Card[] = game.legal_moves || []
  const yourHand = game.hands[String(mySeat)]
  const displayTrick = game.current_trick.length > 0 ? game.current_trick : (heldTrick ?? [])

  const handleCardClick = (card: Card) => {
    if (!yourTurn) return
    if (selectedCard?.suit === card.suit && selectedCard?.rank === card.rank) {
      setSelectedCard(null)
      addLog('play', `You play ${card.rank}${SUIT_SYMBOLS[card.suit]}`)
      playCard(card)
    } else {
      setSelectedCard(card)
    }
  }

  const confirmPlay = () => {
    if (!selectedCard || !yourTurn) return
    addLog('play', `You play ${selectedCard.rank}${SUIT_SYMBOLS[selectedCard.suit]}`)
    playCard(selectedCard)
    setSelectedCard(null)
  }

  const handleLeave = () => {
    if (confirm('Leave this game?')) {
      leave()
      navigate('/')
    }
  }

  const renderOpponent = (seat: number, position: 'left' | 'right') => (
    <PlayerHand
      position={position}
      isYou={false}
      hand={game.hands[String(seat)]}
      isCurrentPlayer={game.current_player === seat}
      isDealer={game.dealer === seat}
      gamePhase={game.phase}
      label={names[seat]}
    />
  )

  return (
    <div className="min-h-screen flex flex-col" style={{ background: 'radial-gradient(ellipse at center, #1e6b3c 0%, #0f3d25 100%)' }}>
      {/* Top bar */}
      <div className="flex items-center justify-between px-6 py-3 bg-black bg-opacity-40">
        <div className="text-gray-300 text-sm">
          Room <span className="font-bold tracking-widest text-white">{room.code}</span>
        </div>
        <div className="text-yellow-300 font-bold tracking-wider">BELOT ONLINE</div>
        <button onClick={handleLeave} className="text-red-400 text-sm hover:text-red-300 transition-colors">
          Leave
        </button>
      </div>

      {/* Error toast */}
      <AnimatePresence>
        {error && (
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="mx-auto mt-2 bg-red-800 text-white px-4 py-2 rounded-lg text-sm z-50"
          >
            {error}
            <button onClick={clearError} className="ml-3 underline">dismiss</button>
          </motion.div>
        )}
      </AnimatePresence>

      <div className="flex-1 flex gap-4 p-4">
        <div className="flex-1 flex flex-col gap-2">
          {/* Two opponents across the top */}
          <div className="flex justify-around items-start">
            {renderOpponent(leftSeat, 'left')}
            {renderOpponent(rightSeat, 'right')}
          </div>

          {/* Table */}
          <div
            className="flex-1 relative rounded-2xl border-4 border-green-900"
            style={{
              background: 'radial-gradient(ellipse at center, #2d8a52 0%, #1a5c38 100%)',
              minHeight: 300,
              boxShadow: 'inset 0 0 40px rgba(0,0,0,0.4)',
            }}
          >
            <TrickArea currentTrick={displayTrick} mySeat={mySeat} numPlayers={n} />

            {/* Bidding overlay */}
            <AnimatePresence>
              {game.phase === 'bidding' && (
                <motion.div
                  initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                  className="absolute inset-0 flex items-center justify-center bg-black bg-opacity-40 rounded-2xl p-4"
                >
                  <BiddingPanel
                    availableBids={game.available_bids}
                    currentBid={game.current_bid}
                    bids={game.bids}
                    isYourTurn={isYourBidTurn}
                    playerNames={names}
                  />
                </motion.div>
              )}
            </AnimatePresence>

            {/* Declarations overlay */}
            <AnimatePresence>
              {showDeclarations && Object.keys(game.declarations).length > 0 && (
                <motion.div
                  initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                  className="absolute inset-0 flex items-center justify-center bg-black bg-opacity-50 rounded-2xl p-4"
                >
                  <DeclarationsPanel
                    declarations={game.declarations}
                    winningPlayer={game.declaration_winner}
                    playerNames={names}
                  />
                </motion.div>
              )}
            </AnimatePresence>

            {/* Game finished overlay */}
            <AnimatePresence>
              {game.phase === 'finished' && (
                <motion.div
                  initial={{ opacity: 0, scale: 0.8 }} animate={{ opacity: 1, scale: 1 }}
                  className="absolute inset-0 flex flex-col items-center justify-center bg-black bg-opacity-80 rounded-2xl"
                >
                  <div className="text-4xl font-bold text-yellow-300 mb-4">Game Over!</div>
                  {game.winner !== null && (
                    <div className="text-2xl text-green-400 font-bold mb-4">
                      🏆 {names[game.winner]} wins!
                    </div>
                  )}
                  <div className="text-white space-y-1 mb-6">
                    {Array.from({ length: n }).map((_, seat) => (
                      <div key={seat} className="flex justify-between gap-8 text-lg">
                        <span>{names[seat]}</span>
                        <span className="font-bold">{game.cumulative_scores[String(seat)] ?? 0}</span>
                      </div>
                    ))}
                  </div>
                  <button
                    onClick={() => { leave(); navigate('/') }}
                    className="bg-yellow-400 text-black font-bold px-6 py-2 rounded-full hover:bg-yellow-300"
                  >
                    Back to Home
                  </button>
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* Your hand */}
          <div className="flex flex-col items-center gap-3">
            <PlayerHand
              position="bottom"
              isYou
              hand={yourHand}
              isCurrentPlayer={game.current_player === mySeat}
              isDealer={game.dealer === mySeat}
              legalMoves={legalMoves}
              selectedCard={selectedCard}
              onCardClick={handleCardClick}
              yourTurn={yourTurn}
              gamePhase={game.phase}
              label={`${names[mySeat]} (you)`}
            />

            <AnimatePresence>
              {selectedCard && yourTurn && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: 10 }}
                  className="flex gap-3"
                >
                  <button
                    onClick={confirmPlay}
                    className="bg-yellow-500 text-black font-bold px-6 py-2 rounded-full hover:bg-yellow-400"
                  >
                    Play {selectedCard.rank}{SUIT_SYMBOLS[selectedCard.suit]}
                  </button>
                  <button
                    onClick={() => setSelectedCard(null)}
                    className="bg-gray-700 text-white px-4 py-2 rounded-full hover:bg-gray-600"
                  >
                    Cancel
                  </button>
                </motion.div>
              )}
              {!selectedCard && game.phase === 'playing' && !yourTurn && (
                <div className="text-white text-sm bg-black bg-opacity-50 px-4 py-2 rounded-full animate-pulse">
                  Waiting for {names[game.current_player ?? 0]}…
                </div>
              )}
            </AnimatePresence>
          </div>
        </div>

        {/* Sidebar */}
        <div className="flex flex-col gap-4 w-52">
          <ScoreBoard gameState={game} playerNames={names} mySeat={mySeat} />
          <GameLog entries={logEntries} />

          {game.game_type && (
            <div className="bg-black bg-opacity-70 rounded-xl p-3 text-white text-center">
              <div className="text-xs text-gray-400">Trump</div>
              <div className="text-2xl font-bold text-yellow-300">{GAME_TYPE_LABELS[game.game_type]}</div>
              <div className="text-xs text-gray-400 mt-1">{names[game.declarer]} called</div>
            </div>
          )}

          <div className="bg-black bg-opacity-70 rounded-xl p-3 text-white text-center">
            <div className="text-xs text-gray-400">Trick</div>
            <div className="text-2xl font-bold">{game.trick_number}/8</div>
          </div>
        </div>
      </div>
    </div>
  )
}
