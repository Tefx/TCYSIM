from enum import Enum, IntEnum, auto

from ..callback import CallBack
from ..exception.handling import RORAcquireFail
from ...utils.idx_obj import IndexObject


class ReqType(Enum):
    STORE = auto()
    RETRIEVE = auto()
    ADJUST = auto()
    RELOCATE = auto()


class ReqState(IntEnum):
    INIT = auto()
    READY = auto()
    STARTED = auto()
    REJECTED = auto()
    RESUME_READY = auto()
    RESUMED = auto()
    SYNCED = auto()
    FINISHED = auto()


class Request(IndexObject):
    STATE = ReqState
    TYPE = ReqType

    def __init__(self, req_type, time,
                 box=None,
                 equipment=None,
                 signals=None,
                 block=None,
                 one_time_attemp=False,
                 **attrs):
        super(Request, self).__init__()
        self.req_type = req_type
        self.id = -1
        self.arrival_time = time
        self.ready_time = -1
        self.start_time = -1
        self.finish_time = -1
        self.reject_time = -1
        self.resume_time = -1
        self.sync_time = -1
        self.signals = dict() if signals is None else signals
        self.state = self.STATE.INIT
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
        self.one_time_attemp = one_time_attemp
        self.reject_times = 0
        self.acquire_fails = set()
        self.acquired_positions = []
        self.ops = []
        self.pred = None
        self.succ = None
        self.__dict__.update(attrs)

    def clean(self):
        self.signals = None
        self.acquire_fails = None
        self.acquired_positions = []
        for op in self.ops:
            op.clean()
        self.ops = None

    def link_signal(self, name, callback, *args, **kwargs):
        self.signals[name] = CallBack(callback, *args, **kwargs)

    def ready(self, time):
        if self.state == self.STATE.REJECTED:
            self.state = self.STATE.RESUME_READY
            self.resume_time = time
        else:
            self.state = self.STATE.READY
            self.ready_time = time

    def is_ready(self):
        if self.state == self.STATE.READY or self.state == self.STATE.RESUME_READY:
            if self.req_type == self.TYPE.RETRIEVE:
                return self.box.state != self.box.STATE.RELOCATING
            return True
        return False

    def submit(self, time, ready=True):
        if ready:
            self.ready(time)
        self.block.req_dispatcher.submit_request(time, self)

    def start_or_resume(self, time):
        if self.state == self.STATE.REJECTED:
            self.state = self.STATE.RESUMED
        else:
            self.state = self.STATE.STARTED
        self.start_time = time

    def acquire_stack(self, time, *locations):
        if not self.block.acquire_stack(time, self, *locations):
            raise RORAcquireFail(self)

    def gen_op(self, time):
        for op in self.equipment.req_handler.handle(time, self):
            self.ops.append(op)
            yield op

    def on_reject(self, time):
        self.state = self.STATE.REJECTED
        self.start_time = -1
        self.finish_time = -1
        self.reject_time = time
        self.reject_times += 1
        if not self.one_time_attemp:
            self.submit(time, ready=False)

    def new_successor(self, type, *args, **kwargs):
        req = self.__class__(self.TYPE[type], *args, **kwargs)
        self.succ = req
        req.pred = self
        return req

    def sync(self, time):
        self.state = self.STATE.SYNCED
        # self.sync_time = time

    def is_synced(self):
        return self.state >= self.STATE.SYNCED and self.sync_time >= 0

    def finish_or_fail(self, time):
        if self.state != self.STATE.REJECTED:
            self.state = self.STATE.FINISHED
            self.finish_time = time
        else:
            for pos in self.acquired_positions:
                self.block.release_stack(time, pos)
            self.acquired_positions = []
        # if self.state == self.STATE.FINISHED:
        #     self.clean()

    def on_acquire_fail(self, time, pos_hash):
        self.acquire_fails.add(pos_hash)

    def on_acquire_success(self, time, pos):
        self.acquired_positions.append(pos)

    def on_resource_release(self, time, pos_hash):
        self.acquire_fails.remove(pos_hash)
        if not self.acquire_fails:
            self.ready(time)
        self.equipment.job_scheduler.schedule(time)

    def __repr__(self):
        return "[{}/{}]({}/AT:{:.2f})".format(self.req_type, self.state.name, self.equipment, self.arrival_time)
