from contextlib import contextmanager
from copy import copy
from enum import Enum, auto
from typing import Type

from pesim import Process, TIME_FOREVER
from tcysim.utils import V3
from tcysim.utils.cache import TimeCache
from .scheduler import JobSchedulerBase
from ..event_reason import EventReason
from ..exception.handling import ROREquipmentConflictError, ReqOpRejectionError
from ..layout import EquipmentRangeLayout
from ..motion import Component
from ..operation import OpBuilderBase, OperationABC, BlockingOperationBase
from ..request import ReqHandlerBase, RequestBase

from uuid import uuid4


class EquipmentState(Enum):
    IDLE = auto()
    WORKING = auto()
    BLOCKING = auto()


class Equipment(EquipmentRangeLayout, Process):
    STATE: Type[EquipmentState] = EquipmentState

    ReqHandler: Type[ReqHandlerBase] = NotImplemented
    OpBuilder: Type[OpBuilderBase] = NotImplemented
    # JobScheduler: Type[JobScheduler] = JobScheduler
    JobScheduler: Type[JobSchedulerBase] = NotImplemented

    BoxEquipmentDelta = V3.zero()

    def __init__(self, yard, offset, rotate=0, init_offset=V3.zero(), name=None, **attrs):
        Process.__init__(self, yard.env)
        EquipmentRangeLayout.__init__(self, offset, rotate)
        self.yard = yard
        self.blocks = []
        self.num_blocks = 0
        self.current_op = None
        self.load = None
        self.state = self.STATE.IDLE
        self.next_task = None
        if name is None:
            self.name = str(uuid4())
        else:
            self.name = name
        self.attrs = copy(attrs)
        self.req_handler = self.ReqHandler(self)
        self.op_builder = self.OpBuilder(self)
        self.job_scheduler = self.JobScheduler(self)
        self.last_running_time = -1
        self.guess_components()
        self.set_coord(init_offset, glob=False)

        self._cur_coord = TimeCache(self.cal_cur_coord)

    def guess_components(self):
        self.components = []
        for k in dir(self):
            v = getattr(self, k)
            if isinstance(v, Component):
                v = copy(v)
                setattr(self, k, v)
                self.components.append(v)

    def instance_name(self):
        if self.name is not None:
            return "{}-{}".format(self.__class__.__name__, self.name)
        else:
            return self.__class__.__name__

    @contextmanager
    def save_state(self):
        for component in self.components:
            component.save_state()
        yield
        for component in self.components:
            component.restore_state()

    def cal_cur_coord(self, time):
        self.run_until(self.time)
        v = V3(0, 0, 0)
        for component in self.components:
            v[component.axis] = component.loc
        return v

    def current_coord(self, transform_to=None):
        v = self._cur_coord.get(self.time)
        # self.run_until(self.time)
        # v = V3(0, 0, 0)
        # for component in self.components:
        #     v[component.axis] = component.loc
        return self.transform_to(v, transform_to)

    def brake_coord(self, modes, transform_to=None):
        self.run_until(self.time)
        v = V3(0, 0, 0)
        for component in self.components:
            v[component.axis] = component.brake_loc(modes[component.axis])
        return self.transform_to(v, transform_to)

    def set_coord(self, v, glob=True):
        if glob:
            v = self.coord_g2l(v)
        for component in self.components:
            component.loc = v[component.axis]

    # def attached_box_coord(self, transform_to="g"):
    #     return self.current_coord(transform_to=transform_to)
    #
    # def op_coord_from_box_coord(self, local_coord, transform_to=None):
    #     return self.transform_to(local_coord, transform_to)
    #
    # def prepare_coord_for_op_coord(self, local_coord, transform_to=None):
    #     return self.transform_to(local_coord, transform_to)

    def coord_from_box(self, box_coord, transform_to=None):
        return self.transform_to(box_coord - self.BoxEquipmentDelta, transform_to)

    def prepare_coord(self, op_coord, transform_to=None):
        raise NotImplementedError
        # return self.transform_to(op_coord, transform_to)

    def coord_to_box(self, self_coord=None, transform_to=None):
        if self_coord is None:
            self_coord = self.current_coord()
        return self.transform_to(self_coord + self.BoxEquipmentDelta, transform_to)

    def assign_block(self, block):
        self.blocks.append(block)
        self.num_blocks += 1

    def run_until(self, time):
        if time > self.last_running_time:
            for component in self.components:
                component.run_until(time)
            self.last_running_time = time

    def interrupt(self):
        for component in self.components:
            component.interrupt()
        self.current_op.interrupted = True
        self.activate(-1, EventReason.INTERRUPTED)
        # print(self.time, self, "interrupt", [(c.axis, c.time, c.curr_v) for c in self.components])

    def allow_interruption(self):
        if self.current_op and isinstance(self.current_op, BlockingOperationBase):
            return False
        else:
            self.run_until(self.env.time)
            return all(component.allow_interruption() for component in self.components)

    def nearby_equipments(self):
        for block in self.blocks:
            for equipment in block.equipments:
                if self is not equipment:
                    yield equipment

    @contextmanager
    def lock_state(self, s1, s2=STATE.IDLE):
        self.state = s1
        yield
        self.state = s2

    def wake(self, reason):
        if self.state != self.STATE.WORKING:
            self.activate(-1, reason)

    def ready_for_new_task(self):
        if self.next_task:
            return False
        elif self.state == self.STATE.WORKING:
            return self.allow_interruption()
        else:
            return self.state != self.STATE.BLOCKING

    def submit_task(self, task, from_self=False):
        if isinstance(task, RequestBase):
            task.equipment = self
        self.next_task = task
        if not from_self:
            if self.state == self.STATE.WORKING:
                if self.allow_interruption():
                    self.interrupt()
            elif self.state != self.STATE.BLOCKING:
                self.activate(-1, EventReason.TASK_ARRIVAL)

    def query_new_task(self, time):
        if self.next_task is None:
            self.job_scheduler.schedule(time)

    def _wait(self):
        if not self.next_task:
            op_or_req = self.job_scheduler.on_idle(self.time)
            if op_or_req is not None:
                self.submit_task(op_or_req, from_self=True)
                return self.time, EventReason.TASK_ARRIVAL
            else:
                return TIME_FOREVER, EventReason.LAST
        else:
            return self.next_task.time, EventReason.TASK_ARRIVAL

    def perform_op(self, op, request=None):
        if op.build_and_check(self.time, self.op_builder):
            self.yard.fire_probe('operation.start', op)
            self.state = self.STATE.WORKING
            self.current_op = op
            yield from op.perform(self.yard)
            self.current_op = None
            self.state = self.STATE.IDLE
            self.yard.fire_probe('operation.finish', op)
        else:
            op.cancel(self.yard)
            self.yard.fire_probe('operation.conflict', op)
            if request:
                raise ROREquipmentConflictError(op)

    def handle_request(self, request):
        request.start_or_resume(self.time)
        try:
            self.yard.fire_probe('request.start', request)
            for op in request.gen_op(self.time):
                yield from self.perform_op(op, request)
                if op.interrupted:
                    break
            self.yard.fire_probe('request.succeed', request)
        except ReqOpRejectionError as e:
            self.req_handler.on_reject(self.time, e)
            self.yard.fire_probe('request.rejected', request)
        request.finish_or_fail(self.time)

    def check_interference(self, op):
        return False, None, None

    def _process(self):
        if self.next_task:
            op_or_req = self.next_task
            self.next_task = None
            if isinstance(op_or_req, RequestBase):
                yield from self.handle_request(op_or_req)
            elif isinstance(op_or_req, OperationABC):
                yield from self.perform_op(op_or_req)
            self.query_new_task(self.time)
        yield self.time, EventReason.SCHEDULE.after

    def current_tasks(self):
        if self.current_op:
            if self.current_op.request:
                return self.current_op.request
            else:
                return self.current_op
        return None

    def is_at_idle_position(self):
        return True

    def callback_before_grasp(self, time, op):
        pass

    def callback_after_grasp(self, time, op):
        self.load = op.box

    def callback_before_release(self, time, op):
        self.load = None

    def callback_after_release(self, time, op):
        pass

    def __getattr__(self, item):
        return self.attrs.get(item, None)

    def __repr__(self):
        return "<{}> at {}".format(self.instance_name(), self.current_coord("g"))

    def plot_info(self):
        return None
