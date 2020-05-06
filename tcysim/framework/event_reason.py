from pesim import TIME_PASSED
from enum import Enum, auto


class EventReason(int, Enum):
    def __new__(cls, *args):
        value = args[0] * 2
        obj = int.__new__(cls, value)
        obj._value_ = value
        return obj

    @property
    def before(self):
        return self.value - 1

    @property
    def after(self):
        return self.value + 1

    CALLBACK = auto()
    INTERRUPTED = auto()
    INTERFERENCE_SOLVED = auto()
    OP_FINISHED = auto()
    REQUEST = auto()
    TASK_ARRIVAL = auto()
    SCHEDULE_RESUME = auto()
    SCHEDULE = auto()
    PROBE_ACTION = auto()
    EV_GEN= auto()
    OBSERVE = auto()
    LAST = TIME_PASSED
