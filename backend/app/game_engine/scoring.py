"""
Scoring for 3-player Bulgarian Belot (house rules).

Each round, every player earns raw points = card points from their own tricks
(+10 for winning the last trick) + their declarations (only the best-declaration
holder scores) + their belot (K+Q of trump = 20).

The bid winner ("caller", who chose the trump) is **вътре** ("inside") if any
other player earned more raw points than them that round. When that happens:
  - the player who outscored the caller (the "beater" — the top scorer) takes
    their own points PLUS the caller's points,
  - the caller scores 0,
  - the third player keeps their own points.

Finally every player's round total is **divided by 10 and rounded** (half up) to
get what is added to their running score. First player to 151 wins.
"""
from typing import Dict, List, Optional
from .card import Card, GameType

NUM_PLAYERS = 3


def _round_div10(points: int) -> int:
    """Divide by 10 and round half up (points are non-negative)."""
    return int(points / 10 + 0.5)


def score_trick_cards(cards: List[Card], game_type: GameType) -> int:
    return sum(c.get_value(game_type) for c in cards)


def calculate_round_scores(
    tricks_by_player: Dict[int, List[List[Card]]],
    last_trick_winner: int,
    game_type: GameType,
    declaration_points: Dict[int, int],
    belot_points: Dict[int, int],
    declarer: int,
) -> Dict[str, object]:
    """Calculate per-player scores for one 8-trick round (see module docstring)."""
    card_points: Dict[int, int] = {p: 0 for p in range(NUM_PLAYERS)}
    for player, trick_list in tricks_by_player.items():
        for trick_cards in trick_list:
            card_points[player] += score_trick_cards(trick_cards, game_type)
    card_points[last_trick_winner] += 10

    # Raw round total per player (before any вътре transfer / rounding).
    raw_total: Dict[int, int] = {
        p: card_points[p] + declaration_points.get(p, 0) + belot_points.get(p, 0)
        for p in range(NUM_PLAYERS)
    }

    # Valat (a single player won all 8 tricks) — informational only.
    valat_player: Optional[int] = None
    for player, trick_list in tricks_by_player.items():
        if len(trick_list) == 8:
            valat_player = player
            break

    others = [p for p in range(NUM_PLAYERS) if p != declarer]
    # Top scorer among the other players (lowest seat wins ties).
    beater = min(others, key=lambda o: (-raw_total[o], o))
    inside = raw_total[beater] > raw_total[declarer]

    round_points: Dict[int, int] = dict(raw_total)
    inside_caller: Optional[int] = None
    if inside:
        inside_caller = declarer
        round_points[beater] = raw_total[beater] + raw_total[declarer]
        round_points[declarer] = 0
        # the third player keeps their own (already set from raw_total)
    else:
        beater = None  # no вътре

    final_scores: Dict[int, int] = {p: _round_div10(round_points[p]) for p in range(NUM_PLAYERS)}

    return {
        "card_points": card_points,
        "decl_points": declaration_points,
        "belot_points": belot_points,
        "raw_total": raw_total,
        "round_points": round_points,
        "final_scores": final_scores,
        "inside": inside,
        "inside_caller": inside_caller,
        "beater": beater,
        "valat": valat_player,
    }


def game_winner(cumulative_scores: Dict[int, int], target: int = 151) -> Optional[int]:
    """Return the winning player if any has reached the target, else None.

    If more than one player crosses the target in the same round, the highest
    score wins.
    """
    leaders = [p for p, s in cumulative_scores.items() if s >= target]
    if not leaders:
        return None
    return max(leaders, key=lambda p: cumulative_scores[p])
