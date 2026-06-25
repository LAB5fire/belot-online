"""
3-player Bulgarian Belot game state machine.

Three players (seats 0, 1, 2), each playing for themselves — no teams. A
24-card deck (9–A) is dealt 3-2-(bid)-3: five cards each, bidding on the
five-card hand, then the final three cards. Eight tricks per round, scoring is
per player, first to 151 wins.
"""
from __future__ import annotations
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple

from .card import Card, Suit, Rank, GameType, BID_ORDER, get_trump_suit
from .deck import new_shuffled_deck, deal_initial, deal_final, NUM_PLAYERS
from .rules import determine_trick_winner, get_legal_moves
from .declarations import (
    Declaration, DeclType, find_declarations,
    determine_winning_player, total_declaration_points,
)
from .scoring import calculate_round_scores, game_winner

TARGET_SCORE = 151
TRICKS_PER_ROUND = 8


class GamePhase(str, Enum):
    BIDDING = "bidding"
    DECLARATIONS = "declarations"
    PLAYING = "playing"
    SCORING = "scoring"
    FINISHED = "finished"


@dataclass
class Bid:
    player: int
    game_type: Optional[GameType]  # None = pass


@dataclass
class CompletedTrick:
    cards: List[Tuple[int, Card]]  # (player_idx, card)
    winner: int
    trick_number: int

    def to_dict(self) -> dict:
        return {
            "winner": self.winner,
            "trick_number": self.trick_number,
            "cards": [{"player": p, "card": c.to_dict()} for p, c in self.cards],
        }


@dataclass
class RoundResult:
    round_number: int
    game_type: GameType
    declarer: int
    card_points: Dict[int, int]
    decl_points: Dict[int, int]
    belot_points: Dict[int, int]
    final_scores: Dict[int, int]
    valat: Optional[int]
    inside: bool = False
    hanging: bool = False
    inside_caller: Optional[int] = None
    beater: Optional[int] = None
    hanging_amount: int = 0


class BelotGame:
    """Complete 3-player Bulgarian Belot game. Seats: 0, 1, 2 (each on their own)."""

    NUM_PLAYERS = NUM_PLAYERS

    def __init__(self, game_id: Optional[str] = None):
        self.game_id: str = game_id or str(uuid.uuid4())
        self.phase: GamePhase = GamePhase.BIDDING

        self.round_number: int = 1
        self.cumulative_scores: Dict[int, int] = {i: 0 for i in range(NUM_PLAYERS)}
        self.round_results: List[RoundResult] = []
        # "Висящи" points carried from a tied round to the next round's top scorer.
        self.hanging_points: int = 0

        self.dealer: int = 0
        self.deck: List[Card] = []
        self.hands: Dict[int, List[Card]] = {}
        self.final_dealt: bool = False
        self.bids: List[Bid] = []
        self.current_bidder: int = 0
        self.game_type: Optional[GameType] = None
        self.declarer: int = 0  # player who won the bid (chooses trump)

        self.all_declarations: Dict[int, List[Declaration]] = {i: [] for i in range(NUM_PLAYERS)}
        self.declaration_winner: Optional[int] = None
        self.declarations_revealed: bool = False
        self.belot_announced: Dict[int, bool] = {i: False for i in range(NUM_PLAYERS)}

        self.current_trick: List[Tuple[int, Card]] = []
        # The just-completed trick, kept for display until the next card is led
        # so every player gets to see all three cards (and who won).
        self.last_trick_cards: List[Tuple[int, Card]] = []
        self.tricks_won: Dict[int, List[CompletedTrick]] = {i: [] for i in range(NUM_PLAYERS)}
        self.current_trick_number: int = 1
        self.current_leader: int = 1
        self.last_trick_winner: Optional[int] = None

        self._start_round()

    # ------------------------------------------------------------------ #
    # Round setup                                                          #
    # ------------------------------------------------------------------ #

    def _start_round(self) -> None:
        self.deck = new_shuffled_deck()
        self.hands = deal_initial(self.deck)  # 5 cards each; final 3 after bidding
        self.final_dealt = False
        self.bids = []
        self.current_bidder = (self.dealer + 1) % NUM_PLAYERS
        self.game_type = None
        self.declarer = 0
        self.all_declarations = {i: [] for i in range(NUM_PLAYERS)}
        self.declaration_winner = None
        self.declarations_revealed = False
        self.belot_announced = {i: False for i in range(NUM_PLAYERS)}
        self.current_trick = []
        self.last_trick_cards = []
        self.tricks_won = {i: [] for i in range(NUM_PLAYERS)}
        self.current_trick_number = 1
        self.current_leader = (self.dealer + 1) % NUM_PLAYERS
        self.last_trick_winner = None
        self.phase = GamePhase.BIDDING

    # ------------------------------------------------------------------ #
    # Bidding phase                                                        #
    # ------------------------------------------------------------------ #

    @property
    def current_bid(self) -> Optional[GameType]:
        for bid in reversed(self.bids):
            if bid.game_type is not None:
                return bid.game_type
        return None

    @property
    def available_bids(self) -> List[GameType]:
        cb = self.current_bid
        if cb is None:
            return list(BID_ORDER)
        idx = BID_ORDER.index(cb)
        return BID_ORDER[idx + 1:]

    def place_bid(self, player: int, game_type: Optional[GameType]) -> None:
        if self.phase != GamePhase.BIDDING:
            raise ValueError("Not in bidding phase")
        if player != self.current_bidder:
            raise ValueError(f"Not player {player}'s turn to bid")
        if game_type is not None and game_type not in self.available_bids:
            raise ValueError(f"Bid {game_type} is not higher than current bid")

        self.bids.append(Bid(player=player, game_type=game_type))
        self._advance_bidder()

    def _advance_bidder(self) -> None:
        passes_in_row = 0
        for bid in reversed(self.bids):
            if bid.game_type is None:
                passes_in_row += 1
            else:
                break

        total_bids = len(self.bids)

        # All three players passed with no bid → redeal.
        if total_bids == NUM_PLAYERS and self.current_bid is None:
            self._start_round()
            return

        # A bid stands and the other two have passed after it → bidding is over.
        if self.current_bid is not None and passes_in_row == NUM_PLAYERS - 1:
            self._finalize_bidding()
            return

        self.current_bidder = (self.current_bidder + 1) % NUM_PLAYERS

    def _finalize_bidding(self) -> None:
        winning_bid = None
        for bid in reversed(self.bids):
            if bid.game_type is not None:
                winning_bid = bid
                break

        assert winning_bid is not None
        self.game_type = winning_bid.game_type
        self.declarer = winning_bid.player

        # Deal the final 3 cards, then look for declarations in the full hands.
        deal_final(self.deck, self.hands)
        self.final_dealt = True
        for i in range(NUM_PLAYERS):
            self.all_declarations[i] = find_declarations(
                self.hands[i], i, self.game_type
            )

        self.phase = GamePhase.DECLARATIONS

    # ------------------------------------------------------------------ #
    # Declarations phase                                                   #
    # ------------------------------------------------------------------ #

    def reveal_declarations(self) -> Dict[str, object]:
        if self.phase != GamePhase.DECLARATIONS:
            raise ValueError("Not in declarations phase")

        self.declaration_winner = determine_winning_player(
            self.all_declarations, self.game_type
        )
        self.declarations_revealed = True
        self.phase = GamePhase.PLAYING

        return {
            "declarations": {
                str(p): [d.to_dict() for d in decls]
                for p, decls in self.all_declarations.items()
            },
            "winning_player": self.declaration_winner,
        }

    # ------------------------------------------------------------------ #
    # Playing phase                                                        #
    # ------------------------------------------------------------------ #

    @property
    def current_player(self) -> int:
        if self.phase == GamePhase.BIDDING:
            return self.current_bidder
        if self.phase == GamePhase.PLAYING:
            return (self.current_leader + len(self.current_trick)) % NUM_PLAYERS
        return self.current_leader

    def get_legal_moves(self, player: int) -> List[Card]:
        if self.phase != GamePhase.PLAYING:
            raise ValueError("Not in playing phase")
        if player != self.current_player:
            raise ValueError(f"Not player {player}'s turn")
        return get_legal_moves(self.hands[player], self.current_trick, self.game_type)

    def play_card(self, player: int, card: Card) -> Optional[CompletedTrick]:
        if self.phase != GamePhase.PLAYING:
            raise ValueError("Not in playing phase")
        if player != self.current_player:
            raise ValueError(f"Not player {player}'s turn")

        legal = self.get_legal_moves(player)
        if card not in legal:
            raise ValueError(f"Card {card} is not a legal move")

        # Leading a new trick clears the previously completed trick from display.
        self.last_trick_cards = []

        self._check_belot(player, card)

        self.hands[player].remove(card)
        self.current_trick.append((player, card))

        if len(self.current_trick) == NUM_PLAYERS:
            return self._resolve_trick()
        return None

    def _check_belot(self, player: int, card: Card) -> None:
        if self.game_type in (GameType.NO_TRUMP, GameType.ALL_TRUMP):
            return
        trump_suit = get_trump_suit(self.game_type)
        if trump_suit is None or card.suit != trump_suit:
            return
        if card.rank not in (Rank.KING, Rank.QUEEN):
            return
        if self.belot_announced[player]:
            return

        partner_rank = Rank.QUEEN if card.rank == Rank.KING else Rank.KING
        # Belot = holding both K and Q of trump (the other is still in hand).
        has_other = any(
            c.suit == trump_suit and c.rank == partner_rank
            for c in self.hands[player]
        )
        if has_other:
            self.belot_announced[player] = True

    def _resolve_trick(self) -> CompletedTrick:
        winner = determine_trick_winner(self.current_trick, self.game_type)

        trick_record = CompletedTrick(
            cards=list(self.current_trick),
            winner=winner,
            trick_number=self.current_trick_number,
        )
        self.tricks_won[winner].append(trick_record)
        self.last_trick_winner = winner

        # Keep the three cards visible (in last_trick_cards) until the winner
        # leads the next trick; current_trick itself is cleared so legal-move
        # and turn logic treat the winner as leading a fresh trick.
        self.last_trick_cards = list(self.current_trick)
        self.current_trick = []
        self.current_leader = winner
        self.current_trick_number += 1

        total_tricks = sum(len(v) for v in self.tricks_won.values())
        if total_tricks == TRICKS_PER_ROUND:
            self._end_round()

        return trick_record

    # ------------------------------------------------------------------ #
    # Scoring                                                              #
    # ------------------------------------------------------------------ #

    def _end_round(self) -> None:
        self.phase = GamePhase.SCORING

        belot_pts: Dict[int, int] = {i: 0 for i in range(NUM_PLAYERS)}
        for player, announced in self.belot_announced.items():
            if announced:
                belot_pts[player] += 20

        decl_pts = total_declaration_points(
            self.all_declarations,
            self.game_type,
            self.declaration_winner,
        )

        tricks_by_player: Dict[int, List[List[Card]]] = {i: [] for i in range(NUM_PLAYERS)}
        for player, trick_list in self.tricks_won.items():
            for t in trick_list:
                tricks_by_player[player].append([c for _, c in t.cards])

        result = calculate_round_scores(
            tricks_by_player=tricks_by_player,
            last_trick_winner=self.last_trick_winner if self.last_trick_winner is not None else self.declarer,
            game_type=self.game_type,
            declaration_points=decl_pts,
            belot_points=belot_pts,
            declarer=self.declarer,
            hanging_in=self.hanging_points,
        )
        self.hanging_points = result["hanging_out"]

        round_result = RoundResult(
            round_number=self.round_number,
            game_type=self.game_type,
            declarer=self.declarer,
            card_points=result["card_points"],
            decl_points=result["decl_points"],
            belot_points=result["belot_points"],
            final_scores=result["final_scores"],
            valat=result["valat"],
            inside=result["inside"],
            hanging=result["hanging"],
            inside_caller=result["inside_caller"],
            beater=result["beater"],
            hanging_amount=result["hanging_out"],
        )
        self.round_results.append(round_result)

        for p in range(NUM_PLAYERS):
            self.cumulative_scores[p] = (
                self.cumulative_scores.get(p, 0) + result["final_scores"].get(p, 0)
            )

        winner = game_winner(self.cumulative_scores, target=TARGET_SCORE)
        if winner is not None:
            self.phase = GamePhase.FINISHED
        else:
            self.dealer = (self.dealer + 1) % NUM_PLAYERS
            self.round_number += 1
            self._start_round()

    def advance_round(self) -> None:
        """No-op kept for API symmetry; rounds advance automatically in _end_round."""
        return None

    # ------------------------------------------------------------------ #
    # State export                                                         #
    # ------------------------------------------------------------------ #

    def _serialize_round_result(self, rr: RoundResult) -> dict:
        return {
            "round_number": rr.round_number,
            "game_type": rr.game_type.value if rr.game_type else None,
            "declarer": rr.declarer,
            "card_points": {str(k): v for k, v in rr.card_points.items()},
            "decl_points": {str(k): v for k, v in rr.decl_points.items()},
            "belot_points": {str(k): v for k, v in rr.belot_points.items()},
            "final_scores": {str(k): v for k, v in rr.final_scores.items()},
            "valat": rr.valat,
            "inside": rr.inside,
            "hanging": rr.hanging,
            "inside_caller": rr.inside_caller,
            "beater": rr.beater,
            "hanging_amount": rr.hanging_amount,
        }

    def to_dict(self, viewer: int = 0) -> dict:
        """Serialize game state from `viewer`'s seat. Hides other hands' cards."""
        hands_visible: Dict[str, object] = {}
        for i in range(NUM_PLAYERS):
            if i == viewer:
                hands_visible[str(i)] = [c.to_dict() for c in self.hands[i]]
            else:
                hands_visible[str(i)] = len(self.hands[i])

        legal_moves: List[Card] = []
        if self.phase == GamePhase.PLAYING and self.current_player == viewer:
            legal_moves = get_legal_moves(
                self.hands[viewer], self.current_trick, self.game_type
            )

        current_player: Optional[int] = None
        if self.phase == GamePhase.BIDDING:
            current_player = self.current_bidder
        elif self.phase == GamePhase.PLAYING:
            current_player = self.current_player

        return {
            "game_id": self.game_id,
            "viewer": viewer,
            "num_players": NUM_PLAYERS,
            "phase": self.phase.value,
            "round_number": self.round_number,
            "dealer": self.dealer,
            "current_player": current_player,
            "cumulative_scores": {str(k): v for k, v in self.cumulative_scores.items()},
            "bids": [
                {"player": b.player, "game_type": b.game_type.value if b.game_type else None}
                for b in self.bids
            ],
            "current_bid": self.current_bid.value if self.current_bid else None,
            "available_bids": [gt.value for gt in self.available_bids] if self.phase == GamePhase.BIDDING else [],
            "game_type": self.game_type.value if self.game_type else None,
            "declarer": self.declarer,
            "hands": hands_visible,
            "current_trick": [
                {"player": p, "card": c.to_dict()} for p, c in self.current_trick
            ],
            "last_trick": [
                {"player": p, "card": c.to_dict()} for p, c in self.last_trick_cards
            ],
            "last_trick_winner": self.last_trick_winner,
            "trick_number": self.current_trick_number,
            "tricks_won_count": {str(p): len(v) for p, v in self.tricks_won.items()},
            "declarations": {
                str(p): [d.to_dict() for d in decls]
                for p, decls in self.all_declarations.items()
            } if self.declarations_revealed else {},
            "declaration_winner": self.declaration_winner,
            "last_round": self._serialize_round_result(self.round_results[-1]) if self.round_results else None,
            "legal_moves": [c.to_dict() for c in legal_moves],
            "winner": game_winner(self.cumulative_scores, target=TARGET_SCORE),
        }
