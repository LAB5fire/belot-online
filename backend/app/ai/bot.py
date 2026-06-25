"""
Belot AI Bot player.
Combines Monte Carlo simulation with heuristic fallbacks.
Does NOT see other players' hands — only its own cards and played cards.
"""
from __future__ import annotations
from typing import Dict, List, Optional, Tuple

from ..game_engine.card import Card, GameType, BID_ORDER, get_trump_suit
from ..game_engine.rules import get_legal_moves
from .heuristics import evaluate_bid, heuristic_card_play
from .monte_carlo import monte_carlo_best_move


class BelotBot:
    """
    AI player for Bulgarian Belot.
    Uses Monte Carlo simulation for card play and heuristics for bidding.
    """

    def __init__(
        self,
        player_idx: int,
        difficulty: int = 2,  # 1=easy, 2=medium, 3=hard
    ):
        self.player_idx = player_idx
        self.difficulty = difficulty
        self.played_cards: List[Card] = []

    @property
    def _simulations(self) -> int:
        return {1: 50, 2: 150, 3: 400}.get(self.difficulty, 150)

    def observe_card_played(self, card: Card) -> None:
        if card not in self.played_cards:
            self.played_cards.append(card)

    def choose_bid(
        self,
        hand: List[Card],
        current_bid: Optional[GameType],
        available_bids: List[GameType],
    ) -> Optional[GameType]:
        """Choose a bid or pass (None)."""
        suggested = evaluate_bid(hand)
        if suggested is None:
            return None
        if suggested not in available_bids:
            # Find the highest available bid that is <= suggested
            idx = BID_ORDER.index(suggested)
            candidates = [gt for gt in available_bids if BID_ORDER.index(gt) <= idx]
            if not candidates:
                return None
            return candidates[-1]
        return suggested

    def choose_card(
        self,
        hand: List[Card],
        current_trick: List[Tuple[int, Card]],
        current_leader: int,
        game_type: GameType,
        hand_sizes: Dict[int, int],
        tricks_won: Dict[int, int],
        trick_number: int,
    ) -> Card:
        """Choose the best card to play using Monte Carlo simulation."""
        legal = get_legal_moves(hand, current_trick, game_type)

        if len(legal) == 1:
            return legal[0]

        if self.difficulty == 1:
            # Easy: use pure heuristics
            return heuristic_card_play(
                hand, current_trick, legal, self.player_idx, game_type, self.played_cards
            )

        return monte_carlo_best_move(
            player=self.player_idx,
            hand=list(hand),
            current_trick=list(current_trick),
            current_leader=current_leader,
            game_type=game_type,
            played_cards=list(self.played_cards),
            hand_sizes=hand_sizes,
            tricks_won=dict(tricks_won),
            trick_number=trick_number,
            num_simulations=self._simulations,
        )

    def reset(self) -> None:
        self.played_cards = []
