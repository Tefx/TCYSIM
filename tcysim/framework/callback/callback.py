from pesim import TIME_FOREVER
from tcysim.utils.idx_obj import IncreaseIndexObject


class CallBack(IncreaseIndexObject):
    __slots__ = ["time", "func", "args", "kwargs"]

    def __init__(self, func, *args, **kwargs):
        super(CallBack, self).__init__()
        self.time = TIME_FOREVER
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def __lt__(self, other):
        if self.time < other.time:
            return True
        elif self.time == other.time:
            return hash(self) < hash(other)
        else:
            return False

    def __call__(self, time):
        return self.func(time, *self.args, **self.kwargs)

