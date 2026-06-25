"""
Monte Carlo simulation for Belot AI move selection.

The AI observes only its own cards and all played cards.
Hidden cards are randomly distributed across opponents for each simulation.
"""
from __future__ import annotations
import random
import copy
from typing import Dict, List, Optional, Tuple

from ..game_engine.card import Card, Suit, Rank, GameType, get_trump_suit
from ..game_engine.deck import create_deck
from ..game_engine.rules import get_legal_moves, determine_trick_winner
from .heuristics import heuristic_card_play


class SimulationState:
    """Lightweight game state for Monte Carlo rollouts."""

    __slots__ = (
        "hands", "current_trick", "current_leader",
        "game_type", "tricks_won", "trick_number",
    )

    def __init__(
        self,
        hands: Dict[int, List[Card]],
        current_trick: List[Tuple[int, Card]],
        current_leader: int,
        game_type: GameType,
        tricks_won: Dict[int, int],
        trick_number: int,
    ):
        self.hands = hands
        self.current_trick = current_trick
        self.current_leader = current_leader
        self.game_type = game_type
        self.tricks_won = tricks_won  # team -> count
        self.trick_number = trick_number

    def copy(self) -> SimulationState:
        return SimulationState(
            hands={p: list(h) for p, h in self.hands.items()},
            current_trick=list(self.current_trick),
            current_leader=self.current_leader,
            game_type=self.game_type,
            tricks_won=dict(self.tricks_won),
            trick_number=self.trick_number,
        )


def _current_player(state: SimulationState) -> int:
    return (state.current_leader + len(state.current_trick)) % 4


def _play_card(state: SimulationState, player: int, card: Card) -> Optional[int]:
    """Play a card; return trick winner team if trick is complete."""
    state.hands[player].remove(card)
    state.current_trick.append((player, card))

    if len(state.current_trick) == 4:
        winner = determine_trick_winner(state.current_trick, state.game_type)
        winning_team = winner % 2
        state.tricks_won[winning_team] = state.tricks_won.get(winning_team, 0) + 1
        state.current_trick = []
        state.current_leader = winner
        state.trick_number += 1
        return winning_team
    return None


def _rollout(state: SimulationState, player_team: int) -> float:
    """
    Play out the remaining tricks using heuristics.
    Returns the expected score for player_team (0.0 - 1.0).
    """
    s = state.copy()
    played_cards: List[Card] = []

    while any(len(h) > 0 for h in s.hands.values()):
        current = _current_player(s)
        legal = get_legal_moves(s.hands[current], s.current_trick, s.game_type)
        if not legal:
            break

        card = heuristic_card_play(
            s.hands[current],
            s.current_trick,
            legal,
            current,
            s.game_type,
            played_cards,
        )
        _play_card(s, current, card)
        played_cards.append(card)

    our_tricks = s.tricks_won.get(player_team, 0)
    total_tricks = sum(s.tricks_won.values())
    if total_tricks == 0:
        return 0.5
    return our_tricks / total_tricks


def _distribute_hidden_cards(
    known_hand: List[Card],
    played_cards: List[Card],
    player: int,
    all_hands_known: Dict[int, List[Card]],
) -> Dict[int, List[Card]]:
    """
    Randomly distribute unknown cards to the 3 other players.
    Constraints: player's own hand is fixed; played cards are excluded.
    all_hands_known can have partial info (e.g., card counts per player).
    """
    all_cards = set(create_deck())
    known = set(known_hand) | set(played_cards)

    # Cards in other players' hands (currently in play somewhere)
    for p, h in all_hands_known.items():
        if p == player:
            continue
        known.update(set(h))

    hidden = list(all_cards - known)
    random.shuffle(hidden)

    result: Dict[int, List[Card]] = {player: list(known_hand)}
    other_players = [p for p in range(4) if p != player]

    # Get target hand sizes for other players
    target_sizes = {p: len(all_hands_known.get(p, [])) for p in other_players}

    idx = 0
    for p in other_players:
        count = target_sizes[p]
        if idx + count > len(hidden):
            count = len(hidden) - idx
        result[p] = hidden[idx: idx + count]
        idx += count

    return result


def monte_carlo_best_move(
    player: int,
    hand: List[Card],
    current_trick: List[Tuple[int, Card]],
    current_leader: int,
    game_type: GameType,
    played_cards: List[Card],
    hand_sizes: Dict[int, int],
    tricks_won: Dict[int, int],
    trick_number: int,
    num_simulations: int = 200,
) -> Card:
    """
    Run Monte Carlo simulations to find the best card to play.
    Returns the card with the highest average expected value.
    """
    legal = get_legal_moves(hand, current_trick, game_type)

    if len(legal) == 1:
        return legal[0]

    player_team = player % 2
    move_scores: Dict[Card, float] = {c: 0.0 for c in legal}
    move_counts: Dict[Card, int] = {c: 0 for c in legal}

    for _ in range(num_simulations):
        # Sample a world
        other_hands: Dict[int, List[Card]] = {}
        for p in range(4):
            if p != player:
                other_hands[p] = []  # we don't know

        distributed = _distribute_hidden_cards(
            hand, played_cards, player, other_hands
        )
        # Adjust to match known hand sizes
        for p in range(4):
            if p == player:
                continue
            target = hand_sizes.get(p, len(distributed.get(p, [])))
            distributed[p] = distributed.get(p, [])[:target]

        for move in legal:
            sim_hands = {p: list(h) for p, h in distributed.items()}
            sim_state = SimulationState(
                hands=sim_hands,
                current_trick=list(current_trick),
                current_leader=current_leader,
                game_type=game_type,
                tricks_won=dict(tricks_won),
                trick_number=trick_number,
            )

            # Play the candidate move
            _play_card(sim_state, player, move)

            # Rollout rest of game
            score = _rollout(sim_state, player_team)
            move_scores[move] += score
            move_counts[move] += 1

    # Average scores
    avg = {c: move_scores[c] / max(move_counts[c], 1) for c in legal}
    return max(avg, key=avg.get)


def evaluate_move(
    player: int,
    card: Card,
    hand: List[Card],
    current_trick: List[Tuple[int, Card]],
    current_leader: int,
    game_type: GameType,
    played_cards: List[Card],
    hand_sizes: Dict[int, int],
    tricks_won: Dict[int, int],
    trick_number: int,
    num_simulations: int = 500,
) -> Dict[Card, float]:
    """
    Evaluate ALL legal moves for a position, returning expected value per move.
    Used by the analyzer.
    """
    legal = get_legal_moves(hand, current_trick, game_type)
    player_team = player % 2
    move_scores: Dict[Card, float] = {c: 0.0 for c in legal}

    for _ in range(num_simulations):
        other_hands: Dict[int, List[Card]] = {}
        for p in range(4):
            if p != player:
                other_hands[p] = []

        distributed = _distribute_hidden_cards(hand, played_cards, player, other_hands)
        for p in range(4):
            if p == player:
                continue
            target = hand_sizes.get(p, len(distributed.get(p, [])))
            distributed[p] = distributed.get(p, [])[:target]

        for move in legal:
            sim_hands = {p: list(h) for p, h in distributed.items()}
            sim_state = SimulationState(
                hands=sim_hands,
                current_trick=list(current_trick),
                current_leader=current_leader,
                game_type=game_type,
                tricks_won=dict(tricks_won),
                trick_number=trick_number,
            )
            _play_card(sim_state, player, move)
            score = _rollout(sim_state, player_team)
            move_scores[move] += score / num_simulations

    return move_scores
