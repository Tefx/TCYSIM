from enum import Enum, auto


class OpType(Enum):
    STORE = auto()
    RETRIEVE = auto()
    RESHUFFLE = auto()
    ADJUST = auto()

