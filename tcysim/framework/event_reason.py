from pesim import TIME_PASSED
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
    FOREVER = TIME_PASSED
