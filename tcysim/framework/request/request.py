from copy import copy
from enum import IntEnum, auto

from .type import ReqType
from ..callback import CallBack
from ..exception.handling import RORAcquireFail


class ReqState(IntEnum):
    INIT = auto()
    READY = auto()
    STARTED = auto()
    REJECTED = auto()
    RESUMED = auto()
    RESUME_READY = auto()
    SYNCED = auto()
    FINISHED = auto()


class Request:
    STATE = ReqState

    def __init__(self, req_type, time, box=None, equipment=None, signals=None, block=None, **attrs):
        self.req_type = req_type
        self.id = -1
        self.arrival_time = time
        self.ready_time = -1
        self.start_time = -1
        self.finish_time = -1
        self.signals = dict() if signals is None else signals
        self.state = ReqState.INIT
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
        self.__dict__.update(attrs)

    def link_signal(self, name, callback, *args, **kwargs):
        self.signals[name] = CallBack(callback, *args, **kwargs)

    def ready(self, time):
        if self.state == ReqState.REJECTED:
            self.state = ReqState.RESUME_READY
        else:
            self.state = ReqState.READY
        self.ready_time = time

    def is_ready(self):
        return self.state == ReqState.READY or self.state == ReqState.RESUME_READY

    def submit(self, time, ready=True):
        if ready:
            self.ready(time)
        self.block.req_dispatcher.submit_request(time, self)

    def start_or_resume(self, time):
        if self.state == ReqState.REJECTED:
            self.state = ReqState.RESUMED
        else:
            self.state = ReqState.STARTED
        self.start_time = time

    def acquire_stack(self, time, *locations):
        if not self.block.acquire_stack(time, self, *locations):
            raise RORAcquireFail(self)

    def gen_op(self, time):
        for op in self.equipment.req_handler.handle(time, self):
            self.ops.append(op)
            yield op

    @property
    def TYPE(self):
        return ReqType

    def on_reject(self, time):
        self.state = ReqState.REJECTED
        self.start_time = -1
        self.finish_time = -1
        self.reject_times += 1
        self.submit(time, ready=False)

    def sync(self, time):
        self.state = ReqState.SYNCED

    def finish_or_fail(self, time):
        if self.state != ReqState.REJECTED:
            self.state = ReqState.FINISHED
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
        return "[{}/{}]({}/AT:{:.2f})".format(self.req_type, self.state.name, self.equipment, self.arrival_time)
