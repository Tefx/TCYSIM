from enum import Enum, auto


class ReqType(Enum):
    STORE = auto()
    RETRIEVE = auto()
    ADJUST = auto()
    RELOCATE = auto()
