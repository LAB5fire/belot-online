import { useEffect, useRef } from 'react'

interface LogEntry {
  message: string
  type: 'play' | 'trick' | 'bid' | 'system'
  timestamp: number
}

interface GameLogProps {
  entries: LogEntry[]
}

export function GameLog({ entries }: GameLogProps) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [entries])

  return (
    <div className="bg-black bg-opacity-70 rounded-xl p-3 text-white text-xs h-40 overflow-y-auto">
      <div className="text-gray-400 font-bold mb-2 text-xs uppercase tracking-wide">
        Game Log
      </div>
      {entries.length === 0 && (
        <div className="text-gray-500 italic">Game started...</div>
      )}
      {entries.map((entry, i) => (
        <div
          key={i}
          className={`mb-1 ${
            entry.type === 'trick'
              ? 'text-yellow-400 font-bold'
              : entry.type === 'bid'
              ? 'text-blue-400'
              : entry.type === 'system'
              ? 'text-green-400'
              : 'text-gray-300'
          }`}
        >
          {entry.message}
        </div>
      ))}
      <div ref={bottomRef} />
    </div>
  )
}

export function buildLogEntry(
  type: LogEntry['type'],
  message: string
): LogEntry {
  return { type, message, timestamp: Date.now() }
}
