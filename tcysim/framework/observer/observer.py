from pesim import Process, TIME_FOREVER
from tcysim.framework.priority import Priority


class Observer(Process):
    def __init__(self, yard, start=0, end=TIME_FOREVER, interval=1):
        super(Observer, self).__init__(yard.env)
        self.yard = yard
        self.interval = interval
        self.start = start
        self.end = end

    def on_observe(self):
        raise NotImplementedError

    def _process(self):
        self.yard.run_until(self.time)
        if self.start <= self.time < self.end:
            self.on_observe()

    def _wait(self, priority=Priority.LOG):
        if self.time < self.start:
            return self.start, priority
        elif self.time >= self.end:
            return TIME_FOREVER, priority
        else:
            return self.time + self.interval, priority
