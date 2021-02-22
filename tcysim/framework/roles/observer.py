from collections import deque
from abc import ABC, abstractmethod

from pesim import Process, TIME_FOREVER, TIME_PASSED
from pesim.math_aux import time_le, time_lt
from ..event_reason import EventReason


class ObserverBase(Process, ABC):
    def __init__(self, yard, start=0, end=TIME_FOREVER, interval=1, env=None):
        super(ObserverBase, self).__init__(env or yard.env)
        self.yard = yard
        self.interval = interval
        self.start_time = start
        self.end_time = end

    @abstractmethod
    def on_observe(self):
        pass

    def _process(self):
        if time_le(self.start_time, self.time) and time_lt(self.time, self.end_time):
            self.on_observe()

    def _wait(self):
        if time_lt(self.time, self.start_time):
            return self.start_time, EventReason.OBSERVE
        elif time_le(self.end_time, self.time):
            return TIME_FOREVER, TIME_PASSED
        else:
            return self.time + self.interval, EventReason.OBSERVE


class TimedObserverBase(Process, ABC):
    def __init__(self, yard, *tps, env=None):
        super(TimedObserverBase, self).__init__(env or yard.env)
        self.yard = yard
        self.tps = deque(sorted(tps))

    @abstractmethod
    def on_observe(self):
        pass

    def _process(self):
        self.on_observe()

    def _wait(self):
        if self.tps:
            return self.tps.popleft(), EventReason.OBSERVE
        else:
            return TIME_FOREVER, TIME_PASSED
