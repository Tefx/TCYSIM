from collections import deque
from enum import IntEnum, auto

from pesim import Process, TIME_FOREVER, TIME_REACHED, TIME_PASSED
from ..event_reason import EventReason

class APState(IntEnum):
    IDLE = auto()
    ENTERING = auto()
    WORKING = auto()

class AccessPoint(Process):
    def __init__(self, env, entry_time=0):
        self.queue = deque()
        self.entry_time = entry_time
        self.state = APState.IDLE
        super(AccessPoint, self).__init__(env)

    def _wait(self):
        if self.queue:
            return -1, EventReason.REQUEST
        else:
            return TIME_FOREVER, TIME_PASSED

    def _process(self):
        entry_time = self.queue[0][1]
        self.state = APState.ENTERING
        yield self.time + entry_time, EventReason.REQUEST
        self.state = APState.WORKING
        req = self.queue[0][0]
        # print(self.time, self, "START", self.queue[0], self.queue[0][0].box.id)
        yield from self.handle(self.queue[0][0])
        # print(self.time, self, "COMPLETE", self.queue[0], self.queue[0][0].box.id, req is self.queue[0])
        self.queue.popleft()
        self.state = APState.IDLE

    def handle(self, request):
        request.ready_and_schedule(self.time)
        yield self.time, EventReason.QUERY_STATE
        while not request.is_synced():
            time = request.estimate_sync_time(self.time, self.env)
            if time - self.time > 3600:
                print(time, request.req_type, request.succ, request.equipment.idx, request)
            assert time - self.time < 3600
            assert time != self.time
            yield time, EventReason.QUERY_STATE
            # assert self.time - request.ready_time < 19000

    def submit(self, time, request, skip_queue):
        # print(self.time, self, "SUBMIT", request, skip_queue, request.box.id)
        if not skip_queue:
            if self.queue:
                self.queue.append((request, self.entry_time))
            else:
                self.queue.append((request, 0))
            request.submit(self.time, ready=False)
            if self.state is APState.IDLE:
                self.activate(-1, EventReason.REQUEST)
        else:
            self.queue.appendleft((request, 0))
            request.submit(self.time, ready=True)
            if self.state is not APState.WORKING:
                self.activate(-1, EventReason.REQUEST)
