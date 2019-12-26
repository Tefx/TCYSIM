import heapq
import inspect
import random
from enum import IntEnum, auto

from pesim import Process, TIME_FOREVER
from tcysim.framework.box import Box
from tcysim.framework.priority import Priority


class GeneratorEvent:
    class TYPE(IntEnum):
        BOMB = auto()
        ALLOC = auto()
        STORE = auto()
        RETRIEVE = auto()

    def __init__(self, time, type, *args):
        self.time = time
        self.type = type
        self.args = args

    def __lt__(self, other):
        return (self.time, self.type) < (other.time, other.type)


class ChainedEventBomb(GeneratorEvent):
    def __init__(self, first_time, *args):
        super(ChainedEventBomb, self).__init__(first_time, GeneratorEvent.TYPE.BOMB, *args)

    def trigger(self, time):
        raise NotImplementedError


class BoxGenerator(ChainedEventBomb):
    def next_time(self, time):
        raise NotImplementedError

    def store_time(self, alloc_time):
        raise NotImplementedError

    def retrieve_time(self, store_time):
        raise NotImplementedError

    def new_box(self):
        raise NotImplementedError

    def trigger(self, time):
        box = self.new_box()
        alloc_time = time
        yield GeneratorEvent(alloc_time, GeneratorEvent.TYPE.ALLOC, box)
        store_time = self.store_time(alloc_time)
        yield GeneratorEvent(store_time, GeneratorEvent.TYPE.STORE, box)
        retrieve_time = self.retrieve_time(store_time)
        yield GeneratorEvent(retrieve_time, GeneratorEvent.TYPE.RETRIEVE, box)
        next_time = self.next_time(time)
        yield self.__class__(next_time)


class Generator(Process):
    def __init__(self, yard):
        super(Generator, self).__init__(yard.env)
        self.queue = []
        self.yard = yard

        self.handler = {
            GeneratorEvent.TYPE.ALLOC:    self.on_alloc,
            GeneratorEvent.TYPE.STORE:    self.on_store,
            GeneratorEvent.TYPE.RETRIEVE: self.on_retrieve,
            }

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
            # print("[{:.2f}]<{}>: {}".format(self.time, ev.type.name, ev.args))
            return self.handler[ev.type](*ev.args)

    def on_alloc(self, box):
        if not self.yard.alloc(self.time, box):
            return False
        return True

    def on_store(self, box):
        if box.state < box.STATE_ALLOCATED:
            return False
        lane = random.choice(list(box.block.lanes.values()))
        self.yard.store(self.time, box, lane)
        return True

    def on_retrieve(self, box):
        if box.state < box.STATE_STORING:
            return False
        lane = random.choice(list(box.block.lanes.values()))
        self.yard.retrieve(self.time, box, lane)
        return True

    def _process(self):
        ev = heapq.heappop(self.queue)
        if not self.on_event(ev):
            ev.time += 60
            self.install_or_add(ev)
