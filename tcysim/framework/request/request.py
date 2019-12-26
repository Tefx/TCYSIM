from copy import copy
from enum import Enum, IntEnum, auto

from ..callback import CallBack


class ReqStatus(IntEnum):
    INIT = auto()
    READY = auto()
    STARTED = auto()
    SENTBACK = auto()
    RESUME = auto()
    SYNCED = auto()
    FINISHED = auto()


class Request:
    def __init__(self, req_type, time, box=None, equipment=None, signals=None, block=None, **attrs):
        self.req_type = req_type
        self.arrival_time = time
        self.start_time = -1
        self.finish_time = -1
        self.cb_time = -1
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
        self.opgen = None
        self.access_point = None
        self.attrs = copy(attrs)
        self.last_op = None

    def __getattr__(self, item):
        return self.attrs[item]

    def link_signal(self, name, callback, *args, **kwargs):
        self.signals[name] = CallBack(callback, *args, **kwargs)

    def ready(self, time):
        self.status = ReqStatus.READY

    def start(self, time):
        if self.status == ReqStatus.SENTBACK:
            self.status = ReqStatus.RESUME
        else:
            self.status = ReqStatus.STARTED
        self.start_time = time

    def send_back(self, time, op):
        self.cb_time = time
        self.start_time = -1
        self.finish_time = -1
        self.status = ReqStatus.SENTBACK
        self.last_op = op

    def sync(self, time):
        self.status = ReqStatus.SYNCED

    def finish(self, time):
        if self.status != ReqStatus.SENTBACK:
            self.status = ReqStatus.FINISHED
            self.finish_time = time

    def __str__(self):
        return "[{}/{}]({}/AT:{})".format(self.req_type, self.status.name, self.equipment, self.arrival_time)
