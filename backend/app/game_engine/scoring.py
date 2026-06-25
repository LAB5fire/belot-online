"""
Scoring for 3-player Bulgarian Belot.

This is the "pure individual" variant: there are no teams. Each player banks
their own points every round:

  - card points from the tricks they personally won,
  - +10 for winning the last (8th) trick,
  - their own declarations (only the player with the best declaration scores —
    handled in declarations.py),
  - their own belot (K+Q of trump) = +20,
  - a valat bonus if a single player wins all 8 tricks.

The bid winner only chooses the trump/game type; there is no contract penalty
("вътре") in this variant. First player to reach the target (151) wins.

Everything here is keyed by player index 0/1/2 so house-rule tweaks stay local.
"""
from typing import Dict, List, Optional
from .card import Card, GameType

NUM_PLAYERS = 3
VALAT_BONUS = 90  # awarded to a player who wins all 8 tricks


def score_trick_cards(cards: List[Card], game_type: GameType) -> int:
    return sum(c.get_value(game_type) for c in cards)


def calculate_round_scores(
    tricks_by_player: Dict[int, List[List[Card]]],
    last_trick_winner: int,
    game_type: GameType,
    declaration_points: Dict[int, int],
    belot_points: Dict[int, int],
) -> Dict[str, object]:
    """
    Calculate per-player scores for one 8-trick round.

    tricks_by_player: player -> list of tricks (each trick a list of cards) won.
    last_trick_winner: player index who won the 8th trick (+10 bonus).
    """
    card_points: Dict[int, int] = {p: 0 for p in range(NUM_PLAYERS)}
    for player, trick_list in tricks_by_player.items():
        for trick_cards in trick_list:
            card_points[player] += score_trick_cards(trick_cards, game_type)

    # Last-trick bonus.
    card_points[last_trick_winner] += 10

    # Valat: a single player took all 8 tricks.
    valat_player: Optional[int] = None
    for player, trick_list in tricks_by_player.items():
        if len(trick_list) == 8:
            valat_player = player
            break

    final_scores: Dict[int, int] = {}
    for p in range(NUM_PLAYERS):
        total = (
            card_points[p]
            + declaration_points.get(p, 0)
            + belot_points.get(p, 0)
        )
        if valat_player == p:
            total += VALAT_BONUS
        final_scores[p] = total

    return {
        "card_points": card_points,
        "decl_points": declaration_points,
        "belot_points": belot_points,
        "final_scores": final_scores,
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
