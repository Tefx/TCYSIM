from enum import IntEnum, auto
import random

from tcysim.utils.dispatcher import Dispatcher
from tcysim.framework.roles.generator import ChainedEventBomb, GeneratorEvent, EventHandler, EventGenerator


class BoxEventType(IntEnum):
    BOMB = auto()
    ALLOC = auto()
    STORE = auto()
    RETRIEVE = auto()


class BoxEventHandler(EventHandler):
    @Dispatcher.on(BoxEventType.ALLOC)
    def on_alloc(self, yard, time, box):
        if not yard.alloc(time, box):
            return False
        return True

    @Dispatcher.on(BoxEventType.STORE)
    def on_store(self, yard, time, box):
        if box.state < box.STATE.ALLOCATED:
            return False
        lane = random.choice(list(box.block.lanes.values()))
        yard.store(time, box, lane)
        return True

    @Dispatcher.on(BoxEventType.RETRIEVE)
    def on_retrieve(self, yard, time, box):
        if box.state < box.STATE.STORING:
            return False
        lane = random.choice(list(box.block.lanes.values()))
        yard.retrieve(time, box, lane)
        return True

    def on_fail(self, ev):
        ev.time += 60
        return ev


class BoxGenerator(EventGenerator):
    EventHandler = BoxEventHandler


class BoxBomb(ChainedEventBomb):
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
        yield GeneratorEvent(alloc_time, BoxEventType.ALLOC, box)
        store_time = self.store_time(alloc_time)
        yield GeneratorEvent(store_time, BoxEventType.STORE, box)
        retrieve_time = self.retrieve_time(store_time)
        yield GeneratorEvent(retrieve_time, BoxEventType.RETRIEVE, box)
        next_time = self.next_time(time)
        yield self.__class__(next_time)
