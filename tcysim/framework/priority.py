from pesim import PRIORITY_MAX
from enum import IntEnum, auto


class Priority(IntEnum):
    CALLBACK = auto()
    INTERRUPT = auto()
    INTERFERENCE_RELEASE = auto()
    OP_FINISH = auto()
    REQUEST = auto()
    TASK_ARRIVAL = auto()
    SCHEDULE = auto()
    PROBE = auto()
    OBSERVE = auto()
    FOREVER = PRIORITY_MAX
