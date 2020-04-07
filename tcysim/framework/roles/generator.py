import heapq
from enum import IntEnum, auto

from pesim import Process, TIME_FOREVER

from ..event_reason import EventReason
from tcysim.utils.dispatcher import Dispatcher

class BoxEventType(IntEnum):
    BOMB = auto()

class GeneratorEvent:
    def __init__(self, time, type=None, *args, **kwargs):
        self.time = time
        self.type = type
        self.args = args
        self.kwargs = kwargs

    def __lt__(self, other):
        return (self.time, self.type.value) < (other.time, other.type.value)


class ChainedEventBomb(GeneratorEvent):
    def __init__(self, first_time, *args, **kwargs):
        super(ChainedEventBomb, self).__init__(first_time, type=BoxEventType.BOMB, *args, **kwargs)

    def trigger(self, time):
        raise NotImplementedError


class EventHandler(Dispatcher):
    def handle(self, yard, time, ev):
        return self.dispatch(ev.type.name, "_", yard, time, *ev.args, **ev.kwargs)

    def on_fail(self, ev):
        pass


class EventGenerator(Process):
    EventHandler = EventHandler

    def __init__(self, yard):
        super(EventGenerator, self).__init__(yard.env)
        self.queue = []
        self.yard = yard

        self.handler = self.EventHandler()

    def install_or_add(self, bomb_or_event):
        heapq.heappush(self.queue, bomb_or_event)

    def _wait(self):
        if not self.queue:
            return TIME_FOREVER, EventReason.LAST
        else:
            return self.queue[0].time, EventReason.REQUEST

    def on_event(self, ev: GeneratorEvent):
        if isinstance(ev, ChainedEventBomb):
            for ev2 in ev.trigger(self.time):
                self.install_or_add(ev2)
            return True
        else:
            return self.handler.handle(self.yard, self.time, ev)

    def _process(self):
        ev = heapq.heappop(self.queue)
        if not self.on_event(ev):
            ev = self.handler.on_fail(ev)
            if ev:
                self.install_or_add(ev)
