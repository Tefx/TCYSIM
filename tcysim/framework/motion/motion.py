class Motion:
    def __init__(self, start_time, timespan, v, a, allow_interruption=False):
        self.start_v = v
        self.a = a
        self.start_time = start_time
        self.timespan = timespan
        self.allow_interruption = allow_interruption

    def split(self, time):
        t = time - self.start_time
        m = self.__class__(self.start_time, t, self.start_v, self.a, allow_interruption=self.allow_interruption)
        self.start_v += self.a * t
        self.timespan -= t
        self.start_time = time
        return m

    @property
    def displacement(self):
        return self.start_v * self.timespan + 0.5 * self.a * self.timespan * self.timespan

    @property
    def finish_velocity(self):
        return self.start_v + self.a * self.timespan

    @property
    def finish_time(self):
        return self.start_time + self.timespan

    def __repr__(self):
        return "[MTN]({:.2f}/{:.2f}/{:.2f}/{:.2f}[{}])".format(
            self.start_time, self.timespan,
            self.start_v, self.a, self.allow_interruption)
