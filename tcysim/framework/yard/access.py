from collections import deque

from pesim import Process, TIME_FOREVER, TIME_REACHED, TIME_PASSED
from ..event_reason import EventReason


class AccessPoint(Process):
    def __init__(self, env, entry_time=0):
        self.queue = deque()
        self.entry_time = entry_time
        self.idle = True
        super(AccessPoint, self).__init__(env)

    def _wait(self):
        if self.queue:
            return -1, EventReason.REQUEST
        else:
            return TIME_FOREVER, TIME_PASSED

    def _process(self):
        self.idle = False
        request = self.queue.popleft()
        yield self.time + self.entry_time, EventReason.REQUEST
        yield from self.handle(request)
        self.idle = True

    def handle(self, request):
        request.ready_and_schedule(self.time)
        yield self.time, EventReason.QUERY_STATE
        while not request.is_synced():
            yield request.estimate_sync_time(self.time, self.env), EventReason.QUERY_STATE

    def submit(self, time, request):
        self.queue.append(request)
        request.submit(self.time, ready=False)
        if self.idle:
            self.activate(-1, EventReason.REQUEST)

