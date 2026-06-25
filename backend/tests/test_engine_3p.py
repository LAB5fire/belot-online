"""Tests for the 3-player Belot game engine."""
import random

import pytest

from app.game_engine.game import BelotGame, GamePhase, TARGET_SCORE
from app.game_engine.deck import create_deck, deal_initial, deal_final, NUM_PLAYERS
from app.game_engine.card import GameType, Rank
from app.game_engine.scoring import calculate_round_scores, game_winner


def force_contract(game: BelotGame, gt: GameType = GameType.ALL_TRUMP) -> None:
    """Drive bidding so the first bidder takes `gt`, rest pass, then start play."""
    first = True
    while game.phase == GamePhase.BIDDING:
        p = game.current_player
        if first and game.current_bid is None:
            game.place_bid(p, gt)
            first = False
        else:
            game.place_bid(p, None)
    # The engine pauses at DECLARATIONS until they are revealed (the room
    # manager does this in the live app); mirror that here.
    if game.phase == GamePhase.DECLARATIONS:
        game.reveal_declarations()


class TestDeck:
    def test_24_card_deck_nine_to_ace(self):
        deck = create_deck()
        assert len(deck) == 24
        assert {c.rank for c in deck} == {Rank.NINE, Rank.TEN, Rank.JACK, Rank.QUEEN, Rank.KING, Rank.ACE}
        assert Rank.SEVEN not in {c.rank for c in deck}
        assert Rank.EIGHT not in {c.rank for c in deck}

    def test_staged_deal_5_then_3(self):
        deck = create_deck()
        hands = deal_initial(deck)
        assert all(len(hands[i]) == 5 for i in range(NUM_PLAYERS))
        deal_final(deck, hands)
        assert all(len(hands[i]) == 8 for i in range(NUM_PLAYERS))
        # All 24 cards dealt, no duplicates.
        dealt = [c for h in hands.values() for c in h]
        assert len(dealt) == 24 and len(set(dealt)) == 24


class TestBidding:
    def test_bid_on_five_cards_then_deal_three(self):
        g = BelotGame()
        assert all(len(g.hands[i]) == 5 for i in range(NUM_PLAYERS))
        force_contract(g, GameType.SPADES)
        # After a contract is set, declarations are revealed and play begins.
        assert g.phase == GamePhase.PLAYING
        assert g.game_type == GameType.SPADES
        assert all(len(g.hands[i]) == 8 for i in range(NUM_PLAYERS))

    def test_all_pass_redeals(self):
        g = BelotGame()
        start_round = g.round_number
        # Everyone passes — engine should redeal and stay in bidding.
        for _ in range(NUM_PLAYERS):
            g.place_bid(g.current_player, None)
        assert g.phase == GamePhase.BIDDING
        assert g.round_number == start_round  # same round, fresh deal


class TestPlay:
    def test_tricks_have_three_cards_and_eight_per_round(self):
        random.seed(1)
        g = BelotGame()
        force_contract(g, GameType.ALL_TRUMP)
        tricks_completed = 0
        round_no = g.round_number
        while g.round_number == round_no and g.phase == GamePhase.PLAYING:
            assert len(g.current_trick) < NUM_PLAYERS
            p = g.current_player
            legal = g.get_legal_moves(p)
            assert legal
            g.play_card(p, random.choice(legal))
            if not g.current_trick:
                tricks_completed += 1
            if tricks_completed and g.phase != GamePhase.PLAYING:
                break
        # Eight tricks make a round.
        assert tricks_completed == 8 or g.round_number != round_no


class TestScoring:
    # Helper piles (No Trump values): A=11, 10=10, K=4, Q=3, J=2, 9=0.
    def _piles(self):
        from app.game_engine.card import Card, Suit
        return {
            0: [[Card(Suit.SPADES, Rank.KING), Card(Suit.SPADES, Rank.QUEEN), Card(Suit.SPADES, Rank.JACK)]],  # 9
            1: [[Card(Suit.SPADES, Rank.ACE), Card(Suit.HEARTS, Rank.ACE), Card(Suit.SPADES, Rank.TEN)]],       # 32
            2: [[Card(Suit.HEARTS, Rank.TEN), Card(Suit.HEARTS, Rank.KING), Card(Suit.HEARTS, Rank.QUEEN)]],    # 17
        }

    def test_round_div10_and_keys(self):
        result = calculate_round_scores(
            tricks_by_player=self._piles(),
            last_trick_winner=2,  # +10 -> player 2 = 27
            game_type=GameType.NO_TRUMP,
            declaration_points={0: 0, 1: 0, 2: 0},
            belot_points={0: 0, 1: 0, 2: 0},
            declarer=1,  # caller is the top scorer -> NOT inside
        )
        assert result["card_points"] == {0: 9, 1: 32, 2: 27}
        assert result["inside"] is False
        # Each banks their own /10 (rounded half up): 9->1, 32->3, 27->3
        assert result["final_scores"] == {0: 1, 1: 3, 2: 3}

    def test_vutre_beater_takes_callers_points(self):
        result = calculate_round_scores(
            tricks_by_player=self._piles(),
            last_trick_winner=2,
            game_type=GameType.NO_TRUMP,
            declaration_points={0: 0, 1: 0, 2: 0},
            belot_points={0: 0, 1: 0, 2: 0},
            declarer=0,  # caller (9 pts) is outscored by player 1 (32) -> ВЪТРЕ
        )
        assert result["inside"] is True
        assert result["inside_caller"] == 0
        assert result["beater"] == 1
        # Beater 1 takes own + caller's: 32 + 9 = 41 -> 4; caller 0; third keeps 27 -> 3
        assert result["final_scores"] == {0: 0, 1: 4, 2: 3}

    def test_rounding_thresholds_per_contract(self):
        from app.game_engine.scoring import round_points
        # All Trump rounds up from 4, No Trump from 5, suit from 6.
        assert round_points(84, GameType.ALL_TRUMP) == 9 and round_points(83, GameType.ALL_TRUMP) == 8
        assert round_points(85, GameType.NO_TRUMP) == 9 and round_points(84, GameType.NO_TRUMP) == 8
        assert round_points(86, GameType.SPADES) == 9 and round_points(85, GameType.SPADES) == 8
        # Full contract totals.
        assert round_points(258, GameType.ALL_TRUMP) == 26
        assert round_points(130, GameType.NO_TRUMP) == 13
        assert round_points(162, GameType.SPADES) == 16

    def test_hanging_tie_then_carry_next_round(self):
        from app.game_engine.card import Card, Suit
        # Exact tie between caller (0) and beater (1): both raw 21, player 2 = 14.
        piles = {
            0: [[Card(Suit.SPADES, Rank.ACE), Card(Suit.SPADES, Rank.TEN)]],   # 21
            1: [[Card(Suit.HEARTS, Rank.ACE), Card(Suit.HEARTS, Rank.TEN)]],   # 21
            2: [[Card(Suit.CLUBS, Rank.KING)]],                                # 4 (+10 last trick = 14)
        }
        r1 = calculate_round_scores(
            tricks_by_player=piles, last_trick_winner=2, game_type=GameType.NO_TRUMP,
            declaration_points={0: 0, 1: 0, 2: 0}, belot_points={0: 0, 1: 0, 2: 0},
            declarer=0, hanging_in=0,
        )
        assert r1["hanging"] is True and r1["inside"] is False
        assert r1["inside_caller"] == 0 and r1["beater"] == 1
        assert r1["hanging_out"] == 21  # caller's points hang
        assert r1["final_scores"] == {0: 0, 1: 2, 2: 1}

        # Next round carries 21; declarer 1 is top scorer (31) and collects it.
        piles2 = {
            0: [[Card(Suit.SPADES, Rank.KING)]],                               # 4
            1: [[Card(Suit.SPADES, Rank.ACE), Card(Suit.SPADES, Rank.TEN)]],   # 21 (+10 = 31)
            2: [[Card(Suit.HEARTS, Rank.QUEEN)]],                              # 3
        }
        r2 = calculate_round_scores(
            tricks_by_player=piles2, last_trick_winner=1, game_type=GameType.NO_TRUMP,
            declaration_points={0: 0, 1: 0, 2: 0}, belot_points={0: 0, 1: 0, 2: 0},
            declarer=1, hanging_in=r1["hanging_out"],
        )
        assert r2["inside"] is False and r2["hanging"] is False
        assert r2["hanging_out"] == 0
        # Player 1: 31 + 21 carried = 52 -> 5 (No Trump). Others round to 0.
        assert r2["final_scores"][1] == 5

    def test_game_winner_highest_over_target(self):
        assert game_winner({0: 100, 1: 100, 2: 100}, TARGET_SCORE) is None
        assert game_winner({0: 151, 1: 90, 2: 80}, TARGET_SCORE) == 0
        assert game_winner({0: 152, 1: 160, 2: 80}, TARGET_SCORE) == 1


class TestFullGame:
    def test_random_self_play_terminates_with_winner(self):
        random.seed(123)
        for s in range(50):
            random.seed(s)
            g = BelotGame()
            guard = 0
            while g.phase != GamePhase.FINISHED:
                guard += 1
                assert guard < 5000
                if g.phase == GamePhase.BIDDING:
                    p = g.current_player
                    if g.current_bid is None and random.random() < 0.7:
                        g.place_bid(p, random.choice(g.available_bids))
                    else:
                        g.place_bid(p, None)
                elif g.phase == GamePhase.DECLARATIONS:
                    g.reveal_declarations()
                elif g.phase == GamePhase.PLAYING:
                    p = g.current_player
                    g.play_card(p, random.choice(g.get_legal_moves(p)))
            w = g.to_dict()["winner"]
            assert w is not None
            assert g.cumulative_scores[w] >= TARGET_SCORE


def test_state_hides_other_hands():
    g = BelotGame()
    force_contract(g, GameType.ALL_TRUMP)
    state = g.to_dict(viewer=2)
    assert isinstance(state["hands"]["2"], list)
    assert isinstance(state["hands"]["0"], int)
    assert isinstance(state["hands"]["1"], int)
    assert state["viewer"] == 2
    assert state["num_players"] == 3
