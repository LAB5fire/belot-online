"""
Deck and dealing for 3-player Bulgarian Belot.

The 3-player variant uses a 24-card deck (ranks 9, 10, J, Q, K, A — the 7s and
8s are removed). Since 7 and 8 are worth 0 points in every game type, all point
totals and trump/belot values are identical to the standard 32-card game.

Dealing follows the classic 3-2-(bid)-3 sequence:
  - deal 5 cards to each player (3 then 2),
  - players bid on their 5-card hand,
  - deal the final 3 cards to each player → 8 cards each (24 cards, no talon).
"""
import random
from typing import List, Dict
from .card import Card, Suit, Rank

NUM_PLAYERS = 3
HAND_SIZE = 8
INITIAL_DEAL = 5  # cards dealt before bidding (3 + 2)

# 3-player Belot deck: 9, 10, J, Q, K, A only.
DECK_RANKS = [Rank.NINE, Rank.TEN, Rank.JACK, Rank.QUEEN, Rank.KING, Rank.ACE]
ALL_SUITS = list(Suit)


def create_deck() -> List[Card]:
    return [Card(suit, rank) for suit in ALL_SUITS for rank in DECK_RANKS]


def shuffle_deck(deck: List[Card]) -> List[Card]:
    shuffled = deck[:]
    random.shuffle(shuffled)
    return shuffled


def new_shuffled_deck() -> List[Card]:
    return shuffle_deck(create_deck())


def deal_initial(deck: List[Card]) -> Dict[int, List[Card]]:
    """Deal the first 5 cards to each of the 3 players (bidding hands)."""
    assert len(deck) == NUM_PLAYERS * HAND_SIZE
    hands: Dict[int, List[Card]] = {i: [] for i in range(NUM_PLAYERS)}
    for i in range(NUM_PLAYERS * INITIAL_DEAL):
        hands[i % NUM_PLAYERS].append(deck[i])
    return hands


def deal_final(deck: List[Card], hands: Dict[int, List[Card]]) -> None:
    """Deal the remaining 3 cards to each player, mutating `hands` in place."""
    start = NUM_PLAYERS * INITIAL_DEAL
    for j in range(start, len(deck)):
        hands[(j - start) % NUM_PLAYERS].append(deck[j])
