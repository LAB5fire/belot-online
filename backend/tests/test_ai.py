"""Tests for the AI system.

The AI module is intentionally set aside in the 3-player online build (kept on
disk but not wired into the app, and the engine now uses a 24-card deck), so
this whole module is skipped.
"""
import pytest

pytest.skip(
    "AI module is set aside in the 3-player online build",
    allow_module_level=True,
)

from app.game_engine.card import Card, Suit, Rank, GameType
from app.ai.bot import BelotBot
from app.ai.heuristics import evaluate_bid, heuristic_card_play, hand_strength
from app.ai.monte_carlo import monte_carlo_best_move


class TestHeuristics:
    def test_evaluate_bid_strong_trump_hand(self):
        hand = [
            Card(Suit.HEARTS, Rank.JACK),
            Card(Suit.HEARTS, Rank.NINE),
            Card(Suit.HEARTS, Rank.ACE),
            Card(Suit.HEARTS, Rank.KING),
            Card(Suit.HEARTS, Rank.QUEEN),
            Card(Suit.SPADES, Rank.ACE),
            Card(Suit.CLUBS, Rank.ACE),
            Card(Suit.DIAMONDS, Rank.ACE),
        ]
        bid = evaluate_bid(hand)
        assert bid is not None

    def test_evaluate_bid_weak_hand_returns_none(self):
        hand = [
            Card(Suit.HEARTS, Rank.SEVEN),
            Card(Suit.HEARTS, Rank.EIGHT),
            Card(Suit.SPADES, Rank.SEVEN),
            Card(Suit.SPADES, Rank.EIGHT),
            Card(Suit.CLUBS, Rank.SEVEN),
            Card(Suit.CLUBS, Rank.EIGHT),
            Card(Suit.DIAMONDS, Rank.SEVEN),
            Card(Suit.DIAMONDS, Rank.EIGHT),
        ]
        bid = evaluate_bid(hand)
        assert bid is None

    def test_hand_strength_all_aces(self):
        hand = [
            Card(Suit.HEARTS, Rank.ACE),
            Card(Suit.SPADES, Rank.ACE),
            Card(Suit.CLUBS, Rank.ACE),
            Card(Suit.DIAMONDS, Rank.ACE),
        ]
        strength = hand_strength(hand, GameType.HEARTS)
        assert strength > 0.1  # 4 aces: only the hearts ace is trump in a hearts game

    def test_heuristic_play_only_legal(self):
        hand = [
            Card(Suit.HEARTS, Rank.JACK),
            Card(Suit.HEARTS, Rank.NINE),
        ]
        legal = list(hand)
        trick = [(1, Card(Suit.SPADES, Rank.ACE))]
        played = []
        chosen = heuristic_card_play(hand, trick, legal, 0, GameType.SPADES, played)
        assert chosen in hand


class TestBot:
    def test_bot_choose_bid_strong_hand(self):
        bot = BelotBot(1, difficulty=2)
        hand = [
            Card(Suit.SPADES, Rank.JACK),
            Card(Suit.SPADES, Rank.NINE),
            Card(Suit.SPADES, Rank.ACE),
            Card(Suit.SPADES, Rank.TEN),
            Card(Suit.SPADES, Rank.KING),
            Card(Suit.HEARTS, Rank.ACE),
            Card(Suit.CLUBS, Rank.ACE),
            Card(Suit.DIAMONDS, Rank.ACE),
        ]
        from app.game_engine.card import BID_ORDER
        bid = bot.choose_bid(hand, None, BID_ORDER)
        assert bid is not None  # Strong hand should bid

    def test_bot_choose_card_legal(self):
        bot = BelotBot(1, difficulty=1)  # Easy for speed
        hand = [
            Card(Suit.HEARTS, Rank.ACE),
            Card(Suit.HEARTS, Rank.TEN),
            Card(Suit.SPADES, Rank.KING),
        ]
        trick = []
        card = bot.choose_card(
            hand=hand,
            current_trick=trick,
            current_leader=1,
            game_type=GameType.HEARTS,
            hand_sizes={0: 8, 1: 8, 2: 8, 3: 8},
            tricks_won={0: 0, 1: 0},
            trick_number=1,
        )
        assert card in hand

    def test_bot_observes_played_cards(self):
        bot = BelotBot(1)
        card = Card(Suit.HEARTS, Rank.ACE)
        bot.observe_card_played(card)
        assert card in bot.played_cards

    def test_bot_reset(self):
        bot = BelotBot(1)
        bot.observe_card_played(Card(Suit.HEARTS, Rank.ACE))
        bot.reset()
        assert len(bot.played_cards) == 0


class TestMonteCarlo:
    def test_monte_carlo_returns_legal_card(self):
        hand = [
            Card(Suit.HEARTS, Rank.ACE),
            Card(Suit.HEARTS, Rank.TEN),
            Card(Suit.SPADES, Rank.JACK),
        ]
        card = monte_carlo_best_move(
            player=0,
            hand=hand,
            current_trick=[],
            current_leader=0,
            game_type=GameType.SPADES,
            played_cards=[],
            hand_sizes={0: 3, 1: 3, 2: 3, 3: 3},
            tricks_won={0: 0, 1: 0},
            trick_number=1,
            num_simulations=20,  # Fast for test
        )
        assert card in hand

    def test_monte_carlo_single_legal_returns_it(self):
        hand = [Card(Suit.HEARTS, Rank.ACE)]
        card = monte_carlo_best_move(
            player=0,
            hand=hand,
            current_trick=[(1, Card(Suit.HEARTS, Rank.KING))],
            current_leader=1,
            game_type=GameType.HEARTS,
            played_cards=[],
            hand_sizes={0: 1, 1: 1, 2: 1, 3: 1},
            tricks_won={0: 0, 1: 0},
            trick_number=8,
            num_simulations=10,
        )
        assert card == hand[0]
