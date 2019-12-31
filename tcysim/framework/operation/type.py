from enum import Enum, auto


class OpType(Enum):
    STORE = auto()
    RETRIEVE = auto()
    RELOCATE = auto()
    MOVE = auto()

