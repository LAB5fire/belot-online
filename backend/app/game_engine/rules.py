"""
Bulgarian Belot valid-move rules (3-player variant — no partnerships).

Follow-suit obligations:
1. Player MUST follow the led suit if possible.
2. If cannot follow suit AND game has a trump suit AND player holds trump cards:
   - Player MUST play a trump card.
   - If playing trump: player MUST beat the current winning trump if possible.
     (With no teams there is no "partner is winning" exemption — you always
     over-trump when you can.)
3. If none of the above apply, player may play any card.
"""
from typing import List, Optional, Tuple
from .card import Card, Suit, GameType, get_trump_suit


def _current_trick_winner(trick: List[Tuple[int, Card]], game_type: GameType) -> Optional[Card]:
    """Return the currently winning card of a trick in progress."""
    if not trick:
        return None
    led_suit = trick[0][1].suit
    winning_card = trick[0][1]
    winning_is_trump = winning_card.is_trump(game_type)

    for _, card in trick[1:]:
        card_is_trump = card.is_trump(game_type)
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

    # Cannot follow suit
    if all_trump:
        # All cards are trump; must beat winner if possible
        current_winner = _current_trick_winner(trick, game_type)
        current_power = current_winner.get_trick_power(game_type) if current_winner else -1
        beating = [c for c in hand if c.get_trick_power(game_type) > current_power]
        return beating if beating else list(hand)

    if trump_suit is None:
        # No trump game — may play anything
        return list(hand)

    # Suit game, cannot follow led suit
    trump_cards = [c for c in hand if c.suit == trump_suit]
    if not trump_cards:
        return list(hand)

    # Must play trump; must beat the current trump winner if possible (no
    # partnerships in the 3-player game, so always over-trump when able).
    winning_card = _current_trick_winner(trick, game_type)

    if winning_card and winning_card.is_trump(game_type):
        current_power = winning_card.get_trick_power(game_type)
        beating_trumps = [
            c for c in trump_cards if c.get_trick_power(game_type) > current_power
        ]
        return beating_trumps if beating_trumps else trump_cards

    return trump_cards


def determine_trick_winner(
    trick: List[Tuple[int, Card]], game_type: GameType
) -> int:
    """Return the player index who wins the trick."""
    if not trick:
        raise ValueError("Empty trick")

    led_suit = trick[0][1].suit
    winning_player = trick[0][0]
    winning_card = trick[0][1]
    winning_is_trump = winning_card.is_trump(game_type)

    for player_idx, card in trick[1:]:
        card_is_trump = card.is_trump(game_type)
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
