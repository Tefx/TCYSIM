from heapq import heappush, heappop

from pesim import TIME_FOREVER, Process
from .callback import CallBack
from ..priority import Priority


class CallBackManager(Process):
    def __init__(self, yard):
        self.yard = yard
        self.queue = []
        super(CallBackManager, self).__init__(yard.env)

    def add(self, callback: CallBack):
        heappush(self.queue, callback)
        if self.queue[0] == callback:
            self.activate(callback.time, Priority.CALLBACK)

    def add_callback(self, time, func, *args, **kwargs):
        cb = CallBack(func, *args, **kwargs)
        cb.time = time
        self.add(cb)

    def _wait(self, priority=Priority.CALLBACK):
        if self.queue:
            return self.queue[0].time, Priority.CALLBACK
        else:
            return TIME_FOREVER, Priority.FOREVER

    def _process(self):
        callback = heappop(self.queue)
        self.yard.fire_probe(self.time, "callback.before", callback)
        callback(self.time)
        self.yard.fire_probe(self.time, "callback.after", callback)
