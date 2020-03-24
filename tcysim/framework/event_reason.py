from pesim import TIME_PASSED
from enum import IntEnum, auto


class EventReason(IntEnum):
    CALLBACK = auto()
    INTERRUPTED = auto()
    INTERFERENCE_SOLVED = auto()
    OP_FINISHED = auto()
    REQUEST = auto()
    TASK_ARRIVAL = auto()
    SCHEDULE = auto()
    PROBE_ACTION = auto()
    OBSERVE = auto()
    LAST = TIME_PASSED
