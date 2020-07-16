class TimeCache:
    def __init__(self, func):
        self.func = func
        self._obj = None
        self.time = -1

    def __getitem__(self, time):
        if time > self.time:
            self.time = time
            self._obj = self.func(time)
        return self._obj

    def get(self, time):
        if time > self.time:
            self.time = time
            self._obj = self.func(time)
        return self._obj
