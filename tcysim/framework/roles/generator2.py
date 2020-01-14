import heapq
from pesim import Process, TIME_FOREVER

from ..priority import Priority
from tcysim.utils.dispatcher import Dispatcher


class EventHandlingFail(Exception):
    pass


class GeneratorEvent:
    def __init__(self, time, type=None, *args, **kwargs):
        self.time = time
        self.type = type
        self.args = args
        self.kwargs = kwargs

    def __lt__(self, other):
        return (self.time, self.type.value) < (other.time, other.type.value)


class EventHandler(Dispatcher):
    def __init__(self, generator):
        super(EventHandler, self).__init__()
        self.generator = generator
        self.yard = generator.yard

    def handle(self, time, ev):
        return self.dispatch(ev.type, "_", time, *ev.args, **ev.kwargs)

    def on_fail(self, ev):
        raise ev from ev


class EventGenerator(Process):
    EventHandler = EventHandler

    def __init__(self, yard, stop_time=TIME_FOREVER):
        super(EventGenerator, self).__init__(yard.env)
        self.queue = []
        self.yard = yard
        self.stop_time = stop_time
        self.handler = self.EventHandler(self)

    def install_or_add(self, event):
        heapq.heappush(self.queue, event)

    def initial_events(self):
        yield from []

    def _wait(self, priority=Priority.REQUEST):
        if not self.queue:
            return TIME_FOREVER, Priority.FOREVER
        else:
            return self.queue[0].time, Priority.REQUEST

    def on_event(self, ev: GeneratorEvent):
        try:
            yield from self.handler.handle(self.time, ev)
        except EventHandlingFail as e:
            yield from self.handler.on_fail(e)

    def _process(self):
        ev = heapq.heappop(self.queue)
        for ev2 in self.on_event(ev):
            if ev2.time < self.stop_time:
                self.install_or_add(ev2)

    def setup(self):
        self.queue = list(self.initial_events())
        heapq.heapify(self.queue)
        super(EventGenerator, self).setup()