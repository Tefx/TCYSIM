from copy import copy
from enum import IntEnum, auto

from ..callback import CallBack


class ReqStatus(IntEnum):
    INIT = auto()
    READY = auto()
    STARTED = auto()
    REJECTED = auto()
    RESUMED = auto()
    RESUME_READY = auto()
    SYNCED = auto()
    FINISHED = auto()


class Request:
    def __init__(self, req_type, time, box=None, equipment=None, signals=None, block=None, **attrs):
        self.req_type = req_type
        self.id = -1
        self.arrival_time = time
        self.ready_time = -1
        self.start_time = -1
        self.finish_time = -1
        self.signals = dict() if signals is None else signals
        self.status = ReqStatus.INIT
        self.box = box
        self.equipment = equipment
        if block is not None:
            self.block = block
        elif box is not None:
            self.block = box.block
        elif equipment is not None:
            self.block = equipment.blocks[0]
        else:
            self.block = None
        self.access_point = None
        self.reject_times = 0
        self.acquire_fails = set()
        self.acquired_positions = []
        self.ops = []
        self.attrs = copy(attrs)

    def __getattr__(self, item):
        return self.attrs[item]

    def link_signal(self, name, callback, *args, **kwargs):
        self.signals[name] = CallBack(callback, *args, **kwargs)

    def ready(self, time):
        if self.status == ReqStatus.REJECTED:
            self.status = ReqStatus.RESUME_READY
        else:
            self.status = ReqStatus.READY
        self.ready_time = time

    def is_ready(self):
        return self.status == ReqStatus.READY or self.status == ReqStatus.RESUME_READY

    def start_or_resume(self, time):
        if self.status == ReqStatus.REJECTED:
            self.status = ReqStatus.RESUMED
        else:
            self.status = ReqStatus.STARTED
        self.start_time = time

    def acquire_stack(self, time, *locations):
        return self.block.acquire_stack(time, self, *locations)

    def gen_op(self, time):
        for op in self.equipment.req_handler.handle(time, self):
            self.ops.append(op)
            yield op

    @property
    def TYPE(self):
        return self.block.req_builder.ReqType

    def on_reject(self, time):
        self.status = ReqStatus.REJECTED
        self.start_time = -1
        self.finish_time = -1
        self.reject_times += 1

    def sync(self, time):
        self.status = ReqStatus.SYNCED

    def finish_or_fail(self, time):
        if self.status != ReqStatus.REJECTED:
            self.status = ReqStatus.FINISHED
            self.finish_time = time
        else:
            for pos in self.acquired_positions:
                self.block.release_stack(time, pos)
            self.acquired_positions = []

    def on_acquire_fail(self, time, pos_hash):
        self.acquire_fails.add(pos_hash)

    def on_acquire_success(self, time, pos):
        self.acquired_positions.append(pos)

    def on_resource_release(self, time, pos_hash):
        self.acquire_fails.remove(pos_hash)
        if not self.acquire_fails:
            self.ready(time)

    def __repr__(self):
        return "[{}/{}]({}/AT:{:.2f})".format(self.req_type, self.status.name, self.equipment, self.arrival_time)
