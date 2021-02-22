from pesim import TIME_FOREVER, MinPairingHeapNode
from pesim.math_aux import time_lt, time_eq


class CallBack(MinPairingHeapNode):
    __slots__ = ["time", "func", "args", "kwargs", "id"]
    __id: int = 0

    def __init__(self, func, *args, **kwargs):
        super(CallBack, self).__init__()
        self.time = TIME_FOREVER
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.id = self.__class__.__id
        self.__class__.__id += 1

    def key_lt(self, other):
        if time_lt(self.time, other.time):
            return True
        elif time_eq(self.time, other.time):
            return self.id < other.id
        else:
            return False

    def __call__(self, time, debug):
        if debug:
            print(self.time, self.func, self.args, self.kwargs)
        res = self.func(time, *self.args, **self.kwargs)
        if debug:
            print(self.func, "done:", res)
        return res

