from enum import Enum
from typing import Optional, Dict, List


class Suit(str, Enum):
    CLUBS = "clubs"
    DIAMONDS = "diamonds"
    HEARTS = "hearts"
    SPADES = "spades"


class Rank(str, Enum):
    SEVEN = "7"
    EIGHT = "8"
    NINE = "9"
    TEN = "10"
    JACK = "J"
    QUEEN = "Q"
    KING = "K"
    ACE = "A"


class GameType(str, Enum):
    CLUBS = "clubs"
    DIAMONDS = "diamonds"
    HEARTS = "hearts"
    SPADES = "spades"
    NO_TRUMP = "no_trump"
    ALL_TRUMP = "all_trump"


SUIT_SYMBOLS: Dict[Suit, str] = {
    Suit.CLUBS: "♣",
    Suit.DIAMONDS: "♦",
    Suit.HEARTS: "♥",
    Suit.SPADES: "♠",
}

BID_ORDER: List[GameType] = [
    GameType.CLUBS,
    GameType.DIAMONDS,
    GameType.HEARTS,
    GameType.SPADES,
    GameType.NO_TRUMP,
    GameType.ALL_TRUMP,
]

TRUMP_CARD_VALUES: Dict[Rank, int] = {
    Rank.JACK: 20,
    Rank.NINE: 14,
    Rank.ACE: 11,
    Rank.TEN: 10,
    Rank.KING: 4,
    Rank.QUEEN: 3,
    Rank.EIGHT: 0,
    Rank.SEVEN: 0,
}

NORMAL_CARD_VALUES: Dict[Rank, int] = {
    Rank.ACE: 11,
    Rank.TEN: 10,
    Rank.KING: 4,
    Rank.QUEEN: 3,
    Rank.JACK: 2,
    Rank.NINE: 0,
    Rank.EIGHT: 0,
    Rank.SEVEN: 0,
}

# Trick-winning power order (index = power, higher index = stronger)
TRUMP_TRICK_ORDER: List[Rank] = [
    Rank.SEVEN, Rank.EIGHT, Rank.QUEEN, Rank.KING,
    Rank.TEN, Rank.ACE, Rank.NINE, Rank.JACK,
]

NORMAL_TRICK_ORDER: List[Rank] = [
    Rank.SEVEN, Rank.EIGHT, Rank.NINE, Rank.JACK,
    Rank.QUEEN, Rank.KING, Rank.TEN, Rank.ACE,
]

NATURAL_ORDER: List[Rank] = [
    Rank.SEVEN, Rank.EIGHT, Rank.NINE, Rank.TEN,
    Rank.JACK, Rank.QUEEN, Rank.KING, Rank.ACE,
]

# Declaration value rankings for 4-of-a-kind
FOUR_OF_A_KIND_ORDER: List[Rank] = [
    Rank.QUEEN, Rank.KING, Rank.TEN, Rank.ACE, Rank.NINE, Rank.JACK
]


def get_trump_suit(game_type: GameType) -> Optional[Suit]:
    mapping = {
        GameType.CLUBS: Suit.CLUBS,
        GameType.DIAMONDS: Suit.DIAMONDS,
        GameType.HEARTS: Suit.HEARTS,
        GameType.SPADES: Suit.SPADES,
    }
    return mapping.get(game_type)


def total_card_points(game_type: GameType) -> int:
    if game_type == GameType.NO_TRUMP:
        return 130
    elif game_type == GameType.ALL_TRUMP:
        return 258
    else:
        return 162


class Card:
    __slots__ = ("suit", "rank")

    def __init__(self, suit: Suit, rank: Rank):
        self.suit = suit
        self.rank = rank

    def get_value(self, game_type: GameType) -> int:
        trump_suit = get_trump_suit(game_type)
        is_trump = game_type == GameType.ALL_TRUMP or (
            trump_suit is not None and self.suit == trump_suit
        )
        return TRUMP_CARD_VALUES[self.rank] if is_trump else NORMAL_CARD_VALUES[self.rank]

    def get_trick_power(self, game_type: GameType) -> int:
        trump_suit = get_trump_suit(game_type)
        is_trump = game_type == GameType.ALL_TRUMP or (
            trump_suit is not None and self.suit == trump_suit
        )
        return (
            TRUMP_TRICK_ORDER.index(self.rank)
            if is_trump
            else NORMAL_TRICK_ORDER.index(self.rank)
        )

    def is_trump(self, game_type: GameType) -> bool:
        if game_type == GameType.ALL_TRUMP:
            return True
        trump_suit = get_trump_suit(game_type)
        return trump_suit is not None and self.suit == trump_suit

    def natural_index(self) -> int:
        return NATURAL_ORDER.index(self.rank)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Card):
            return self.suit == other.suit and self.rank == other.rank
        return False

    def __hash__(self) -> int:
        return hash((self.suit, self.rank))

    def __repr__(self) -> str:
        return f"{self.rank.value}{SUIT_SYMBOLS[self.suit]}"

    def to_dict(self) -> dict:
        return {"suit": self.suit.value, "rank": self.rank.value}

    @classmethod
    def from_dict(cls, d: dict) -> "Card":
        return cls(Suit(d["suit"]), Rank(d["rank"]))
