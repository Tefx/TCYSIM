from abc import ABC
from enum import Enum, IntEnum, auto, Flag
from typing import Type

from pesim.math_aux import time_eq, time_lt

from pesim import TIME_FOREVER
from ..callback import CallBack
from ...utils.idx_obj import IndexObject


class ReqType(Enum):
    STORE = auto()
    RETRIEVE = auto()


# class ReqState(IntEnum):
#     INIT = auto()
#     READY = auto()
#     SCHEDULED = auto()
#     STARTED = auto()
#     REJECTED = auto()
#     RESUME_READY = auto()
#     RESUMED = auto()
#     SYNCED = auto()
#     FINISHED = auto()

class ReqState(Flag):
    INIT = auto()
    READY = auto()
    SCHEDULED = auto()
    STARTED = auto()
    REJECTED = auto()
    RESUME_READY = auto()
    # RESUMED = auto()
    SYNCED = auto()
    FINISHED = auto()

    PENDING_FLAG = INIT | REJECTED
    SYNCED_FLAG = SYNCED | FINISHED
    # RUNNING_FLAG = SYNCED | RESUMED | STARTED
    RUNNING_FLAG = SYNCED | STARTED
    SCHEDULED_FLAG = SCHEDULED | RUNNING_FLAG | FINISHED
    READY_FLAG = READY | RESUME_READY | RUNNING_FLAG | FINISHED


class RequestBase(IndexObject):
    TYPE: Type[Enum] = NotImplemented
    STATE: Type[Flag] = ReqState

    gid = 0

    def __init__(self, req_type, time,
                 box=None,
                 equipment=None,
                 signals=None,
                 block=None,
                 one_time_attempt=False,
                 **attrs):
        super(RequestBase, self).__init__()
        self.req_type = req_type
        self.id = RequestBase.gid
        RequestBase.gid += 1
        self.create_time = time
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
        self.ap = None
        if block is not None:
            self.block = block
        elif box is not None:
            self.block = box.block
        elif equipment is not None:
            self.block = equipment.blocks[0]
        else:
            self.block = None
        self.access_point = None
        self.one_time_attempt = one_time_attempt
        self.reject_times = 0
        self.ops = []
        self.__dict__.update(attrs)

    def clean(self):
        self.signals = None
        for op in self.ops:
            op.clean()
        self.ops = None

    def link_signal(self, name, callback, *args, **kwargs):
        self.signals[name] = CallBack(callback, *args, **kwargs)

    def ready(self, time):
        if not self.state & self.STATE.READY_FLAG:
            if self.state == self.STATE.REJECTED:
                self.state = self.STATE.RESUME_READY
                self.resume_time = time
            else:
                self.state = self.STATE.READY
                self.ready_time = time

    def schedule(self, time):
        if self.equipment:
            self.equipment.job_scheduler.schedule(time)
        else:
            for equipment in self.block.equipments:
                equipment.job_scheduler.schedule(time)

    def ready_and_schedule(self, time):
        self.ready(time)
        self.schedule(time)

    def is_ready_for(self, equipment):
        return self.state & self.STATE.READY_FLAG
        # return self.state == self.STATE.READY or self.state == self.STATE.RESUME_READY

    def submit(self, time, ready=True):
        if ready:
            self.ready(time)
        self.block.req_dispatcher.submit_request(time, self)

    def start_or_resume(self, time):
        # if self.state == self.STATE.REJECTED:
        #     self.state = self.STATE.RESUMED
        # else:
        self.state = self.STATE.STARTED
        self.start_time = time

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
        if not self.one_time_attempt:
            self.submit(time, ready=False)

    def on_scheduled(self, time):
        pass

    def sync(self, time):
        self.state = self.STATE.SYNCED
        # self.sync_time = time

    def is_running_or_scheduled(self):
        return self.state & self.STATE.SCHEDULED_FLAG

    def is_synced(self):
        return self.state & self.STATE.SYNCED_FLAG and self.sync_time >= 0

    def finish_or_fail(self, time):
        if self.state != self.STATE.REJECTED:
            self.state = self.STATE.FINISHED
            self.finish_time = time

    # def estimate_sync_time(self, time, env):
    #     if self.state & self.STATE.RUNNING_FLAG:
    #         if self.sync_time > 0:
    #             return self.sync_time
    #         else:
    #             next_time = self.equipment.next_event_time()
    #             if time_eq(TIME_FOREVER, next_time):
    #                 next_time = min(e.next_event_time() for e in self.block.equipments)
    #                 if time_eq(TIME_FOREVER, next_time):
    #                     for equipment in self.block.yard.equipments:
    #                         next_time = min(next_time, equipment.next_event_time())
    #     else:
    #         if self.equipment is not None:
    #             next_time = self.equipment.next_event_time()
    #             if time_eq(TIME_FOREVER, next_time):
    #                 next_time = min(e.next_event_time() for e in self.block.equipments)
    #                 if time_eq(TIME_FOREVER, next_time):
    #                     for equipment in self.block.yard.equipments:
    #                         next_time = min(next_time, equipment.next_event_time())
    #         elif self.block is not None:
    #             next_time = min(eqp.next_event_time() for eqp in self.block.equipments)
    #             if time_eq(TIME_FOREVER, next_time):
    #                 for equipment in self.block.yard.equipments:
    #                     next_time = min(next_time, equipment.next_event_time())
    #         else:
    #             next_time = env.next_event_time()
    #     return next_time

    def estimate_sync_time(self, time, env):
        if self.state & self.STATE.RUNNING_FLAG and self.sync_time > 0:
            return self.sync_time

        search_list = []
        if self.equipment:
            search_list.append((self.equipment,))
        if self.block:
            search_list.append(self.block.equipments)
            search_list.append(self.block.yard.equipments)
        search_list.append((env,))

        for processes in search_list:
            next_time = TIME_FOREVER
            for proc in processes:
                cur_nt = proc.next_event_time()
                if time_lt(cur_nt, next_time):
                    next_time = cur_nt
            if time_lt(next_time, TIME_FOREVER):
                return next_time

        return TIME_FOREVER

    def __repr__(self):
        return "[{}/{}]({}/AT:{:.2f})".format(self.req_type, self.state.name, self.equipment, self.create_time)
