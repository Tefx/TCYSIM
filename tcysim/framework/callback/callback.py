from pesim import TIME_FOREVER


class CallBack:
    def __init__(self, func, *args, **kwargs):
        self.time = TIME_FOREVER
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def __lt__(self, other):
        return self.time < other.time

    def __call__(self, time):
        return self.func(time, *self.args, **self.kwargs)

