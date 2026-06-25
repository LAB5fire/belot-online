"""
Fast heuristic evaluation functions for Belot AI.
Used both for quick move selection and Monte Carlo playouts.
"""
from typing import List, Optional, Dict, Tuple
from ..game_engine.card import Card, Suit, Rank, GameType, get_trump_suit, TRUMP_CARD_VALUES, NORMAL_CARD_VALUES


def hand_strength(hand: List[Card], game_type: GameType) -> float:
    """Evaluate hand strength 0-1 for a given game type."""
    if not hand:
        return 0.0
    total = sum(c.get_value(game_type) for c in hand)
    trump_cards = [c for c in hand if c.is_trump(game_type)]
    trump_count = len(trump_cards)
    trump_value = sum(c.get_value(game_type) for c in trump_cards)
    score = total * 0.5 + trump_count * 8 + trump_value * 0.3
    return min(1.0, score / 200.0)


def evaluate_bid(hand: List[Card]) -> Optional[GameType]:
    """
    Simple heuristic: return the best game type to bid for this hand,
    or None if the hand is too weak to bid.
    """
    from ..game_engine.card import GameType, BID_ORDER

    best_gt = None
    best_score = -1

    for gt in BID_ORDER:
        score = _bid_score(hand, gt)
        if score > best_score and score >= 0.35:
            best_score = score
            best_gt = gt

    return best_gt


def _bid_score(hand: List[Card], game_type: GameType) -> float:
    trump_cards = [c for c in hand if c.is_trump(game_type)]
    trump_count = len(trump_cards)
    trump_pts = sum(c.get_value(game_type) for c in trump_cards)
    total_pts = sum(c.get_value(game_type) for c in hand)

    if game_type == GameType.ALL_TRUMP:
        # Need many high trumps
        return (trump_pts / 258.0) * 0.7 + (trump_count / 8.0) * 0.3
    elif game_type == GameType.NO_TRUMP:
        # Need high cards in multiple suits
        return (total_pts / 130.0) * 0.8 + (trump_count == 0) * 0.05
    else:
        # Suit game - need 4+ trumps with good values
        if trump_count < 3:
            return 0.0
        return (trump_pts / 162.0) * 0.6 + (trump_count / 8.0) * 0.4


def heuristic_card_play(
    hand: List[Card],
    trick: List[Tuple[int, Card]],
    legal_moves: List[Card],
    player: int,
    game_type: GameType,
    played_cards: List[Card],
) -> Card:
    """
    Fast heuristic for choosing a card to play.
    Used in Monte Carlo simulations.
    """
    if len(legal_moves) == 1:
        return legal_moves[0]

    partner = (player + 2) % 4
    partner_winning = _is_partner_winning(trick, partner, game_type)
    leading = len(trick) == 0

    if leading:
        return _choose_lead(hand, legal_moves, game_type, played_cards)

    if partner_winning:
        return _play_when_partner_winning(legal_moves, game_type)

    return _play_to_win(hand, trick, legal_moves, game_type, played_cards)


def _is_partner_winning(
    trick: List[Tuple[int, Card]], partner: int, game_type: GameType
) -> bool:
    if not trick:
        return False
    from ..game_engine.rules import determine_trick_winner
    current_winner = _get_current_winner(trick, game_type)
    if current_winner is None:
        return False
    for p, c in trick:
        if p == partner and c == current_winner:
            return True
    return False


def _get_current_winner(
    trick: List[Tuple[int, Card]], game_type: GameType
) -> Optional[Card]:
    if not trick:
        return None
    led_suit = trick[0][1].suit
    winning = trick[0][1]
    winning_is_trump = winning.is_trump(game_type)

    for _, card in trick[1:]:
        ct = card.is_trump(game_type)
        if ct and not winning_is_trump:
            winning = card
            winning_is_trump = True
        elif ct and winning_is_trump:
            if card.get_trick_power(game_type) > winning.get_trick_power(game_type):
                winning = card
        elif not ct and not winning_is_trump and card.suit == led_suit:
            if card.get_trick_power(game_type) > winning.get_trick_power(game_type):
                winning = card
    return winning


def _choose_lead(
    hand: List[Card],
    legal: List[Card],
    game_type: GameType,
    played: List[Card],
) -> Card:
    """Lead with the strongest card in the best suit."""
    # Prefer leading with trump if many trumps remain
    trump_legal = [c for c in legal if c.is_trump(game_type)]
    non_trump_legal = [c for c in legal if not c.is_trump(game_type)]

    if game_type == GameType.ALL_TRUMP:
        # Always lead trump
        return max(legal, key=lambda c: c.get_trick_power(game_type))

    if trump_legal and len(trump_legal) >= 3:
        # Lead highest trump to draw opponent trumps
        return max(trump_legal, key=lambda c: c.get_trick_power(game_type))

    # Lead with highest card in a suit we dominate
    if non_trump_legal:
        # Find best non-trump lead (aces, 10s are valuable)
        aces = [c for c in non_trump_legal if c.rank == Rank.ACE]
        if aces:
            return aces[0]
        tens = [c for c in non_trump_legal if c.rank == Rank.TEN]
        if tens:
            return tens[0]
        return max(non_trump_legal, key=lambda c: c.get_value(game_type))

    return max(legal, key=lambda c: c.get_value(game_type))


def _play_when_partner_winning(legal: List[Card], game_type: GameType) -> Card:
    """Partner is winning, so dump a low-value card or a valuable one to score points."""
    # Play highest value card (partner will win the trick, earn those points)
    return max(legal, key=lambda c: c.get_value(game_type))


def _play_to_win(
    hand: List[Card],
    trick: List[Tuple[int, Card]],
    legal: List[Card],
    game_type: GameType,
    played: List[Card],
) -> Card:
    """Try to win the trick; if can't, dump lowest value card."""
    current_best = _get_current_winner(trick, game_type)
    current_power = current_best.get_trick_power(game_type) if current_best else -1
    current_is_trump = current_best.is_trump(game_type) if current_best else False

    led_suit = trick[0][1].suit if trick else None

    winning_cards = []
    for card in legal:
        card_is_trump = card.is_trump(game_type)
        if card_is_trump and not current_is_trump:
            winning_cards.append(card)
        elif card_is_trump and current_is_trump:
            if card.get_trick_power(game_type) > current_power:
                winning_cards.append(card)
        elif not card_is_trump and not current_is_trump and card.suit == led_suit:
            if card.get_trick_power(game_type) > current_power:
                winning_cards.append(card)

    if winning_cards:
        # Win with the cheapest winning card
        return min(winning_cards, key=lambda c: c.get_value(game_type))

    # Can't win — dump lowest value card
    return min(legal, key=lambda c: c.get_value(game_type))
