from heapq import heappush, heappop

from pesim import TIME_FOREVER, Process
from .callback import CallBack
from ..priority import Priority


class CallBackManager(Process):
    def __init__(self, env):
        self.queue = []
        super(CallBackManager, self).__init__(env)

    def add(self, callback: CallBack):
        heappush(self.queue, callback)
        if self.queue[0] == callback:
            self.activate(callback.time, Priority.CALLBACK)

    def _wait(self, priority=Priority.CALLBACK):
        if self.queue:
            return self.queue[0].time, Priority.CALLBACK
        else:
            return TIME_FOREVER, Priority.FOREVER

    def _process(self):
        callback = heappop(self.queue)
        callback(self.time)
