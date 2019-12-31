import heapq

from pesim import Process, TIME_FOREVER
from tcysim.framework.priority import Priority
from tcysim.utils.dispatcher import Dispatcher


class GeneratorEvent:
    def __init__(self, time, type=None, *args, **kwargs):
        self.time = time
        self.type = type
        self.args = args
        self.kwargs = kwargs

    def __lt__(self, other):
        return (self.time, self.type) < (other.time, other.type)


class ChainedEventBomb(GeneratorEvent):
    def __init__(self, first_time, *args, **kwargs):
        super(ChainedEventBomb, self).__init__(first_time, type=None, *args, **kwargs)

    def trigger(self, time):
        raise NotImplementedError


class EventHandler(Dispatcher):
    def handle(self, yard, time, ev):
        return self.dispatch(ev.type, "_", yard, time, *ev.args, **ev.kwargs)

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

    def _wait(self, priority=Priority.REQUEST):
        if not self.queue:
            return TIME_FOREVER, Priority.FOREVER
        else:
            return self.queue[0].time, Priority.REQUEST

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
