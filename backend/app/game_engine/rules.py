"""
Bulgarian Belot valid-move rules (3-player house variant).

Follow-suit obligations (per the user's house rules):
1. Player MUST follow the led suit if possible.
   - When the led suit is trump (a suit contract led with trump, or All Trump),
     you must over-ride with a higher card of that suit if you can.
2. If you CANNOT follow the led suit, you may play ANY card — you are never
   forced to trump ("цакаш") in any contract. A voluntarily played trump still
   wins the trick as normal.
"""
from typing import List, Optional, Tuple
from .card import Card, Suit, GameType, get_trump_suit


def _is_trump_suit_card(card: Card, game_type: GameType) -> bool:
    """True only for cards of the single trump suit in a suit game.

    In No Trump and All Trump there is no *master* trump suit that beats other
    suits across the trick (All Trump just means every suit uses the trump
    ranking within its own suit), so this returns False for both — only the led
    suit can win those tricks.
    """
    trump_suit = get_trump_suit(game_type)
    return trump_suit is not None and card.suit == trump_suit


def _current_trick_winner(trick: List[Tuple[int, Card]], game_type: GameType) -> Optional[Card]:
    """Return the currently winning card of a trick in progress."""
    if not trick:
        return None
    led_suit = trick[0][1].suit
    winning_card = trick[0][1]
    winning_is_trump = _is_trump_suit_card(winning_card, game_type)

    for _, card in trick[1:]:
        card_is_trump = _is_trump_suit_card(card, game_type)
        if card_is_trump and not winning_is_trump:
            winning_card = card
            winning_is_trump = True
        elif card_is_trump and winning_is_trump:
            if card.get_trick_power(game_type) > winning_card.get_trick_power(game_type):
                winning_card = card
        elif not card_is_trump and not winning_is_trump and card.suit == led_suit:
            if card.get_trick_power(game_type) > winning_card.get_trick_power(game_type):
                winning_card = card

    return winning_card


def get_legal_moves(
    hand: List[Card],
    trick: List[Tuple[int, Card]],
    game_type: GameType,
) -> List[Card]:
    """Return all legal cards a player can play given the current trick."""
    if not trick:
        return list(hand)

    led_suit = trick[0][1].suit
    trump_suit = get_trump_suit(game_type)
    all_trump = game_type == GameType.ALL_TRUMP

    # Cards that follow suit
    follow_suit_cards = [c for c in hand if c.suit == led_suit]

    if follow_suit_cards:
        # Must follow suit
        if all_trump or (trump_suit is not None and led_suit == trump_suit):
            # Led suit IS trump — must beat current winner if possible
            current_winner = _current_trick_winner(trick, game_type)
            current_power = current_winner.get_trick_power(game_type) if current_winner else -1
            beating_cards = [
                c for c in follow_suit_cards
                if c.get_trick_power(game_type) > current_power
            ]
            return beating_cards if beating_cards else follow_suit_cards
        return follow_suit_cards

    # Cannot follow the led suit — you may play any card (no forced trumping
    # in any contract, per the house rules).
    return list(hand)


def determine_trick_winner(
    trick: List[Tuple[int, Card]], game_type: GameType
) -> int:
    """Return the player index who wins the trick."""
    if not trick:
        raise ValueError("Empty trick")

    led_suit = trick[0][1].suit
    winning_player = trick[0][0]
    winning_card = trick[0][1]
    winning_is_trump = _is_trump_suit_card(winning_card, game_type)

    for player_idx, card in trick[1:]:
        card_is_trump = _is_trump_suit_card(card, game_type)
        beats = False

        if card_is_trump and not winning_is_trump:
            beats = True
        elif card_is_trump and winning_is_trump:
            beats = card.get_trick_power(game_type) > winning_card.get_trick_power(game_type)
        elif not card_is_trump and not winning_is_trump and card.suit == led_suit:
            beats = card.get_trick_power(game_type) > winning_card.get_trick_power(game_type)

        if beats:
            winning_player = player_idx
            winning_card = card
            winning_is_trump = card_is_trump

    return winning_player


def is_legal_bid(current_bid: Optional[str], new_bid: str) -> bool:
    """Validate a bid is higher than the current one."""
    from .card import BID_ORDER, GameType
    if current_bid is None:
        return True
    try:
        current_gt = GameType(current_bid)
        new_gt = GameType(new_bid)
        return BID_ORDER.index(new_gt) > BID_ORDER.index(current_gt)
    except ValueError:
        return False
