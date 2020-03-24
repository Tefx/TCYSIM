from pesim import Process, TIME_FOREVER, TIME_PASSED
from ..event_reason import EventReason


class Observer(Process):
    def __init__(self, yard, start=0, end=TIME_FOREVER, interval=1, env=None):
        super(Observer, self).__init__(env or yard.env)
        self.yard = yard
        self.interval = interval
        self.start_time = start
        self.end_time = end

    def on_observe(self):
        raise NotImplementedError

    def _process(self):
        if self.start_time <= self.time < self.end_time:
            self.on_observe()

    def _wait(self):
        if self.time < self.start_time:
            return self.start_time, EventReason.OBSERVE
        elif self.time >= self.end_time:
            return TIME_FOREVER, TIME_PASSED
        else:
            return self.time + self.interval, EventReason.OBSERVE
