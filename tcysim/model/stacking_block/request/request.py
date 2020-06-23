from enum import Enum, auto

from tcysim.framework import RequestBase
from .handler import RORAcquireFail


class RequestForStackingBlock(RequestBase):
    class TYPE(Enum):
        STORE = auto()
        RETRIEVE = auto()
        ADJUST = auto()
        RELOCATE = auto()

    def __init__(self, req_type, time,
                 box=None,
                 equipment=None,
                 signals=None,
                 block=None,
                 one_time_attempt=False,
                 **attrs):
        super(RequestForStackingBlock, self).__init__(req_type, time, box, equipment, signals, block, one_time_attempt, **attrs)
        self.acquire_fails = set()
        self.acquired_positions = []
        self.pred = None
        self.succ = None

    def clean(self):
        self.acquire_fails = None
        self.acquired_positions = []
        super(RequestForStackingBlock, self).clean()

    def is_ready_for(self, equipment):
        if super(RequestForStackingBlock, self).is_ready_for(equipment):
            if self.req_type == self.TYPE.RETRIEVE:
                return self.box.state != self.box.STATE.RELOCATING
            return True
        return False

    def new_successor(self, type, *args, **kwargs):
        req = self.__class__(self.TYPE[type], *args, **kwargs)
        self.succ = req
        req.pred = self
        return req

    def finish_or_fail(self, time):
        if self.state != self.STATE.REJECTED:
            self.state = self.STATE.FINISHED
            self.finish_time = time
        else:
            for pos in self.acquired_positions:
                self.block.release_stack(time, pos)
            self.acquired_positions = []

    def acquire_stack(self, time, *locations):
        if not self.block.acquire_stack(time, self, *locations):
            raise RORAcquireFail(self)

    def on_acquire_fail(self, time, pos_hash):
        self.acquire_fails.add(pos_hash)

    def on_acquire_success(self, time, pos):
        self.acquired_positions.append(pos)

    def on_resource_release(self, time, pos_hash):
        self.acquire_fails.remove(pos_hash)
        if not self.acquire_fails:
            self.ready(time)
        self.equipment.job_scheduler.schedule(time)

