from pesim import TIME_FOREVER, MinPairingHeapNode
from tcysim.utils.idx_obj import IncreaseIndexObject


class CallBack(MinPairingHeapNode):
    __slots__ = ["time", "func", "args", "kwargs", "id"]
    __id = 0

    def __init__(self, func, *args, **kwargs):
        super(CallBack, self).__init__()
        self.time = TIME_FOREVER
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.id = self.__class__.__id
        self.__class__.__id += 1

    def cmp(self, other):
        if self.time < other.time:
            return True
        elif self.time == other.time:
            return self.id < other.id
        else:
            return False

    def __call__(self, time):
        return self.func(time, *self.args, **self.kwargs)

