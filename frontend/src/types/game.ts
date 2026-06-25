export type Suit = 'clubs' | 'diamonds' | 'hearts' | 'spades'
export type Rank = '9' | '10' | 'J' | 'Q' | 'K' | 'A'
export type GameType =
  | 'clubs'
  | 'diamonds'
  | 'hearts'
  | 'spades'
  | 'no_trump'
  | 'all_trump'

export type GamePhase = 'bidding' | 'declarations' | 'playing' | 'scoring' | 'finished'

export interface Card {
  suit: Suit
  rank: Rank
}

export interface Bid {
  player: number
  game_type: GameType | null
}

export interface TrickCard {
  player: number
  card: Card
}

export interface Declaration {
  type: string
  points: number
  player: number
  cards: Card[]
  suit: Suit | null
  top_rank: Rank | null
}

export interface RoundResult {
  round_number: number
  game_type: GameType
  declarer: number
  card_points: Record<string, number>
  decl_points: Record<string, number>
  belot_points: Record<string, number>
  final_scores: Record<string, number>
  valat: number | null
}

export interface GameState {
  game_id: string
  viewer: number
  num_players: number
  phase: GamePhase
  round_number: number
  dealer: number
  current_player: number | null
  cumulative_scores: Record<string, number>
  bids: Bid[]
  current_bid: GameType | null
  available_bids: GameType[]
  game_type: GameType | null
  declarer: number
  hands: Record<string, Card[] | number>
  current_trick: TrickCard[]
  last_trick: TrickCard[]
  last_trick_winner: number | null
  trick_number: number
  tricks_won_count: Record<string, number>
  declarations: Record<string, Declaration[]>
  declaration_winner: number | null
  last_round: RoundResult | null
  legal_moves: Card[]
  winner: number | null
}

export interface RoomPlayer {
  seat: number
  name: string
  connected: boolean
}

export interface RoomMeta {
  code: string
  status: 'lobby' | 'playing' | 'finished'
  host_seat: number
  your_seat: number
  players: RoomPlayer[]
  max_players: number
}

export interface TrickResult {
  winner: number
  trick_number: number
  cards: TrickCard[]
}

export const SUIT_SYMBOLS: Record<Suit, string> = {
  clubs: '♣',
  diamonds: '♦',
  hearts: '♥',
  spades: '♠',
}

export const SUIT_COLORS: Record<Suit, string> = {
  clubs: '#1a1a1a',
  diamonds: '#cc0000',
  hearts: '#cc0000',
  spades: '#1a1a1a',
}

export const GAME_TYPE_LABELS: Record<GameType, string> = {
  clubs: '♣ Clubs',
  diamonds: '♦ Diamonds',
  hearts: '♥ Hearts',
  spades: '♠ Spades',
  no_trump: 'No Trump',
  all_trump: 'All Trump',
}
