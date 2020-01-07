from pesim import TIME_FOREVER


class CallBack:
    gid = 0

    def __init__(self, func, *args, **kwargs):
        self.time = TIME_FOREVER
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.id = self.gid
        self.gid += 1

    def __lt__(self, other):
        if self.time < other.time:
            return True
        elif self.time == other.time:
            return self.id < other.id
        else:
            return False

    def __call__(self, time):
        return self.func(time, *self.args, **self.kwargs)

