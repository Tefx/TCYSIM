from collections import deque

from pesim import Process, TIME_FOREVER, TIME_REACHED, TIME_PASSED
from tcysim.framework.event_reason import EventReason


class AccessPoint(Process):
    def __init__(self, env, enter_time=0):
        super(AccessPoint, self).__init__(env)
        self.queue = deque()
        self.enter_time = enter_time
        self.idle = True

    def _wait(self):
        if self.queue:
            return self.queue[0][0], EventReason.REQUEST
        else:
            return TIME_FOREVER, TIME_PASSED

    def _process(self):
        self.idle = False
        time, request = self.queue.popleft()
        yield self.time + self.enter_time, EventReason.REQUEST
        self.handle(request)
        self.idle = True

    def handle(self, request):
        request.submit(self.time)

    def submit(self, time, request):
        self.queue.append(request)
        if not self.idle:
            self.activate(time, EventReason.REQUEST)

