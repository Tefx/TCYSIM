from pesim.math_aux import flt
from pesim import MinPairingHeap, MinPairingHeapNode, Process, TIME_FOREVER
from tcysim.utils.dispatcher import Dispatcher
from ...event_reason import EventReason


class EventHandlingFail(Exception):
    pass


class GeneratorEvent(MinPairingHeapNode):
    __slots__ = ["time", "type", "args", "reason"]

    def __init__(self, time, type, reason, *args):
        self.time = time
        self.type = type
        self.reason=reason
        self.args = args

    def key_lt(self, other):
        if self.time == other.time:
            return self.type.value < other.type.value
        else:
            return flt(self.time, other.time)


class EventHandler(Dispatcher):
    def __init__(self, generator):
        super(EventHandler, self).__init__()
        self.generator = generator
        self.yard = generator.yard

    def handle(self, time, ev):
        return self.dispatch(ev.type.name, "_", time, *ev.args)

    def on_fail(self, ev):
        raise ev from ev


class EventGenerator(Process):
    EventHandler = EventHandler

    def __init__(self, yard, stop_time=TIME_FOREVER, env=None):
        self.queue = None
        self.yard = yard
        self.stop_time = stop_time
        self.handler = self.EventHandler(self)
        super(EventGenerator, self).__init__(env or yard.env)

    def install_or_add(self, event):
        self.queue.push(event)

    def initial_events(self):
        yield from []

    def _wait(self):
        ev = self.queue.first()
        if ev:
            return ev.time, ev.reason
        else:
            return TIME_FOREVER, EventReason.LAST

    def on_event(self, ev: GeneratorEvent):
        try:
            yield from self.handler.handle(self.time, ev)
        except EventHandlingFail as e:
            yield from self.handler.on_fail(e)

    def stop(self):
        self.queue.clear()

    def _process(self):
        ev = self.queue.pop()
        for ev2 in self.on_event(ev):
            if ev2.time < self.stop_time:
                self.install_or_add(ev2)

    def start(self):
        self.queue = MinPairingHeap(self.initial_events())
        super(EventGenerator, self).start()
