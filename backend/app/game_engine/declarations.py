"""
Bulgarian Belot declarations (combinations announced before play).
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Tuple, Dict
from .card import Card, Suit, Rank, GameType, NATURAL_ORDER, FOUR_OF_A_KIND_ORDER, get_trump_suit


class DeclType(str, Enum):
    TIERCE = "tierce"       # 3 consecutive = 20 pts
    QUART = "quart"         # 4 consecutive = 50 pts
    QUINT = "quint"         # 5+ consecutive = 100 pts
    FOUR_JACKS = "four_jacks"   # 200 pts
    FOUR_NINES = "four_nines"   # 150 pts
    FOUR_ACES = "four_aces"     # 100 pts
    FOUR_TENS = "four_tens"     # 100 pts
    FOUR_KINGS = "four_kings"   # 100 pts
    FOUR_QUEENS = "four_queens" # 100 pts
    BELOT = "belot"         # K+Q of trump = 20 pts (announced during play)


DECL_POINTS = {
    DeclType.TIERCE: 20,
    DeclType.QUART: 50,
    DeclType.QUINT: 100,
    DeclType.FOUR_JACKS: 200,
    DeclType.FOUR_NINES: 150,
    DeclType.FOUR_ACES: 100,
    DeclType.FOUR_TENS: 100,
    DeclType.FOUR_KINGS: 100,
    DeclType.FOUR_QUEENS: 100,
    DeclType.BELOT: 20,
}

FOUR_KIND_RANKS = {
    Rank.JACK: DeclType.FOUR_JACKS,
    Rank.NINE: DeclType.FOUR_NINES,
    Rank.ACE: DeclType.FOUR_ACES,
    Rank.TEN: DeclType.FOUR_TENS,
    Rank.KING: DeclType.FOUR_KINGS,
    Rank.QUEEN: DeclType.FOUR_QUEENS,
}


@dataclass
class Declaration:
    decl_type: DeclType
    cards: List[Card]
    points: int
    player: int
    suit: Optional[Suit] = None  # for sequences
    top_rank: Optional[Rank] = None  # highest card in sequence

    @property
    def is_four_of_kind(self) -> bool:
        return self.decl_type in (
            DeclType.FOUR_JACKS, DeclType.FOUR_NINES,
            DeclType.FOUR_ACES, DeclType.FOUR_TENS,
            DeclType.FOUR_KINGS, DeclType.FOUR_QUEENS,
        )

    @property
    def sequence_length(self) -> int:
        if self.decl_type == DeclType.TIERCE:
            return 3
        elif self.decl_type == DeclType.QUART:
            return 4
        elif self.decl_type == DeclType.QUINT:
            return len(self.cards)
        return 0

    def to_dict(self) -> dict:
        return {
            "type": self.decl_type.value,
            "points": self.points,
            "player": self.player,
            "cards": [c.to_dict() for c in self.cards],
            "suit": self.suit.value if self.suit else None,
            "top_rank": self.top_rank.value if self.top_rank else None,
        }


def find_declarations(hand: List[Card], player: int, game_type: GameType) -> List[Declaration]:
    """Find all declarations in a player's hand."""
    decls: List[Declaration] = []
    trump_suit = get_trump_suit(game_type)

    # Check four-of-a-kind
    by_rank: Dict[Rank, List[Card]] = {}
    for card in hand:
        by_rank.setdefault(card.rank, []).append(card)

    for rank, cards in by_rank.items():
        if len(cards) == 4 and rank in FOUR_KIND_RANKS:
            dt = FOUR_KIND_RANKS[rank]
            decls.append(Declaration(
                decl_type=dt,
                cards=cards,
                points=DECL_POINTS[dt],
                player=player,
            ))

    # Check sequences per suit
    for suit in Suit:
        suit_cards = sorted(
            [c for c in hand if c.suit == suit],
            key=lambda c: NATURAL_ORDER.index(c.rank),
        )
        if len(suit_cards) < 3:
            continue

        # Find consecutive runs
        runs: List[List[Card]] = []
        current_run = [suit_cards[0]]
        for i in range(1, len(suit_cards)):
            prev_idx = NATURAL_ORDER.index(suit_cards[i - 1].rank)
            curr_idx = NATURAL_ORDER.index(suit_cards[i].rank)
            if curr_idx == prev_idx + 1:
                current_run.append(suit_cards[i])
            else:
                if len(current_run) >= 3:
                    runs.append(current_run)
                current_run = [suit_cards[i]]
        if len(current_run) >= 3:
            runs.append(current_run)

        for run in runs:
            length = len(run)
            top_rank = run[-1].rank
            if length >= 5:
                dt = DeclType.QUINT
            elif length == 4:
                dt = DeclType.QUART
            else:
                dt = DeclType.TIERCE

            decls.append(Declaration(
                decl_type=dt,
                cards=run,
                points=DECL_POINTS[dt],
                player=player,
                suit=suit,
                top_rank=top_rank,
            ))

    return decls


def has_belot(hand: List[Card], game_type: GameType) -> bool:
    trump_suit = get_trump_suit(game_type)
    if trump_suit is None:
        return False
    has_king = any(c.suit == trump_suit and c.rank == Rank.KING for c in hand)
    has_queen = any(c.suit == trump_suit and c.rank == Rank.QUEEN for c in hand)
    return has_king and has_queen


def _decl_sort_key(decl: Declaration) -> Tuple:
    """Key for comparing declarations: four-of-a-kind > sequence; then by points/length/rank."""
    if decl.is_four_of_kind:
        rank_order = FOUR_OF_A_KIND_ORDER.index(decl.cards[0].rank) if decl.cards else 0
        return (1, decl.points, rank_order, 0)
    else:
        top_rank_idx = NATURAL_ORDER.index(decl.top_rank) if decl.top_rank else 0
        return (0, decl.points, decl.sequence_length, top_rank_idx)


def best_declaration(decls: List[Declaration]) -> Optional[Declaration]:
    if not decls:
        return None
    return max(decls, key=_decl_sort_key)


def compare_declarations(
    decl_a: Optional[Declaration],
    decl_b: Optional[Declaration],
    game_type: GameType,
) -> int:
    """Returns 1 if a wins, -1 if b wins, 0 if tie (a wins on tie in Bulgarian rules)."""
    if decl_a is None and decl_b is None:
        return 0
    if decl_a is None:
        return -1
    if decl_b is None:
        return 1

    key_a = _decl_sort_key(decl_a)
    key_b = _decl_sort_key(decl_b)

    if key_a > key_b:
        return 1
    elif key_a < key_b:
        return -1

    # Same strength - trump wins
    trump_suit = get_trump_suit(game_type)
    if game_type == GameType.ALL_TRUMP:
        return 0  # Both trump, tie → a wins by convention

    a_trump = decl_a.suit == trump_suit if decl_a.suit else False
    b_trump = decl_b.suit == trump_suit if decl_b.suit else False

    if a_trump and not b_trump:
        return 1
    if b_trump and not a_trump:
        return -1
    return 0  # True tie - first declarer wins


def determine_winning_player(
    all_declarations: Dict[int, List[Declaration]],
    game_type: GameType,
) -> Optional[int]:
    """Return the player who holds the single best declaration, or None.

    In the 3-player (no-teams) variant only one player scores declarations:
    whoever holds the strongest single declaration. Ties go to the earlier
    seat (lower index), matching the "first declarer wins" convention.
    """
    winner: Optional[int] = None
    winner_best: Optional[Declaration] = None

    for player_idx in sorted(all_declarations.keys()):
        player_best = best_declaration(all_declarations[player_idx])
        if player_best is None:
            continue
        if winner_best is None or compare_declarations(player_best, winner_best, game_type) > 0:
            winner = player_idx
            winner_best = player_best

    return winner


def total_declaration_points(
    all_declarations: Dict[int, List[Declaration]],
    game_type: GameType,
    winning_player: Optional[int],
) -> Dict[int, int]:
    """Return declaration points per player (only the winner scores)."""
    points = {p: 0 for p in all_declarations}
    if winning_player is None:
        return points

    for d in all_declarations.get(winning_player, []):
        if d.decl_type != DeclType.BELOT:
            points[winning_player] += d.points

    return points
