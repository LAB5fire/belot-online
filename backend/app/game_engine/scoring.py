"""
Scoring for 3-player Bulgarian Belot (house rules).

Each round, every player earns raw points = card points from their own tricks
(+10 for winning the last trick) + their declarations (only the best-declaration
holder scores) + their belot (K+Q of trump = 20).

The bid winner ("caller", who chose the trump) is compared against the best of
the other two players ("beater"):

  - beater > caller  → ВЪТРЕ ("inside"): the beater takes their own points PLUS
    the caller's points; the caller scores 0; the third player keeps their own.
  - beater == caller → ВИСЯЩИ ("hanging"): the caller scores 0 and the caller's
    points are set aside ("hang"); the beater and the third player keep their
    own. The hanging points are carried into the NEXT round and awarded to
    whoever takes the most points that round.
  - beater < caller  → caller is safe; everyone keeps their own.

Each player's round total is then divided by 10 and rounded. The rounding
threshold for the last digit depends on the contract (because the totals
differ): All Trump rounds up from 4, No Trump from 5, a suit game from 6.
First player to 151 wins.
"""
from typing import Dict, List, Optional
from .card import Card, GameType

NUM_PLAYERS = 3

# Last-digit threshold at/above which the score rounds up, per contract.
ROUND_THRESHOLD = {
    GameType.ALL_TRUMP: 4,
    GameType.NO_TRUMP: 5,
    GameType.CLUBS: 6,
    GameType.DIAMONDS: 6,
    GameType.HEARTS: 6,
    GameType.SPADES: 6,
}


def round_points(points: int, game_type: GameType) -> int:
    """Divide by 10 and round using the contract-specific last-digit threshold."""
    threshold = ROUND_THRESHOLD.get(game_type, 6)
    return points // 10 + (1 if points % 10 >= threshold else 0)


def score_trick_cards(cards: List[Card], game_type: GameType) -> int:
    return sum(c.get_value(game_type) for c in cards)


def calculate_round_scores(
    tricks_by_player: Dict[int, List[List[Card]]],
    last_trick_winner: int,
    game_type: GameType,
    declaration_points: Dict[int, int],
    belot_points: Dict[int, int],
    declarer: int,
    hanging_in: int = 0,
) -> Dict[str, object]:
    """Calculate per-player scores for one 8-trick round (see module docstring).

    `hanging_in` is any "висящи" points carried from the previous round; the
    returned `hanging_out` is what should be carried into the next round.
    """
    card_points: Dict[int, int] = {p: 0 for p in range(NUM_PLAYERS)}
    for player, trick_list in tricks_by_player.items():
        for trick_cards in trick_list:
            card_points[player] += score_trick_cards(trick_cards, game_type)
    card_points[last_trick_winner] += 10

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
    beater = min(others, key=lambda o: (-raw_total[o], o))  # top other, ties→lowest seat

    round_points_raw: Dict[int, int] = dict(raw_total)
    inside = False
    hanging = False
    inside_caller: Optional[int] = None
    beater_out: Optional[int] = None
    hanging_out = 0

    if raw_total[beater] > raw_total[declarer]:
        inside = True
        inside_caller = declarer
        beater_out = beater
        round_points_raw[beater] = raw_total[beater] + raw_total[declarer]
        round_points_raw[declarer] = 0
    elif raw_total[beater] == raw_total[declarer]:
        hanging = True
        inside_caller = declarer
        beater_out = beater
        round_points_raw[declarer] = 0
        hanging_out = raw_total[declarer]  # caller's points hang for next round

    # Award any carried-in hanging points to whoever took the most this round.
    if hanging_in > 0:
        top = min(range(NUM_PLAYERS), key=lambda p: (-round_points_raw[p], p))
        round_points_raw[top] += hanging_in

    final_scores: Dict[int, int] = {
        p: round_points(round_points_raw[p], game_type) for p in range(NUM_PLAYERS)
    }

    return {
        "card_points": card_points,
        "decl_points": declaration_points,
        "belot_points": belot_points,
        "raw_total": raw_total,
        "round_points": round_points_raw,
        "final_scores": final_scores,
        "inside": inside,
        "hanging": hanging,
        "inside_caller": inside_caller,
        "beater": beater_out,
        "hanging_in": hanging_in,
        "hanging_out": hanging_out,
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
