from enum import Enum, auto


class OpType(Enum):
    STORE = auto()
    RETRIEVE = auto()
    RELOCATE = auto()
    ADJUST = auto()
    MOVE = auto()

