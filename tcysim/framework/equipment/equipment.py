from contextlib import contextmanager
from copy import copy
from enum import Enum, auto

from pesim import TIME_FOREVER, Process
from ..exception.handling import ReqOpRejectionError, ROREquipmentConflictError
from ..operation import Operation
from ..priority import Priority
from ..layout import EquipmentRangeLayout
from tcysim.utils import V3
from .req_handler import ReqHandler
from .op_builder import OpBuilder
from ..request import Request
from ..scheduler.scheduler import JobScheduler


class EquipmentState(Enum):
    IDLE = auto()
    WORKING = auto()
    BLOCKING = auto()


class Equipment(EquipmentRangeLayout, Process):
    STATE = EquipmentState

    ReqHandler = ReqHandler
    OpBuilder = OpBuilder
    JobScheduler = JobScheduler

    GRASP_TIME = 5
    RELEASE_TIME = 5

    def __init__(self, yard, components, offset, move_range, rotate=0, init_offset=V3.zero(), **attrs):
        Process.__init__(self, yard.env)
        EquipmentRangeLayout.__init__(self, offset, move_range, rotate)
        self.yard = yard
        self.blocks = []
        self.num_blocks = 0
        self.current_op = None
        self.state = self.STATE.IDLE
        self.next_task = None
        self.components = [copy(item) for item in components]
        self.set_coord(init_offset, glob=False)
        self.attrs = copy(attrs)
        self.req_handler = self.ReqHandler(self)
        self.op_builder = self.OpBuilder(self)
        self.job_scheduler = self.JobScheduler(self)
        self.last_running_time = -1

    def setup(self):
        super(Equipment, self).setup()
        self.job_scheduler.setup()

    @contextmanager
    def save_state(self):
        for component in self.components:
            component.save_state()
        yield
        for component in self.components:
            component.restore_state()

    def current_coord(self, transform_to=None):
        self.run_until(self.env.current_time)
        v = V3(0, 0, 0)
        for component in self.components:
            v[component.axis] = component.loc
        return self.transform_to(v, transform_to)

    def set_coord(self, v, glob=True):
        if glob:
            v = self.coord_g2l(v)
        for component in self.components:
            component.loc = v[component.axis]

    def attached_box_coord(self, transform_to="g"):
        return self.current_coord(transform_to=transform_to)

    def op_coord_from_box_coord(self, local_coord, transform_to=None):
        return self.transform_to(local_coord, transform_to)

    def prepare_coord_for_op_coord(self, local_coord, transform_to=None):
        return self.transform_to(local_coord, transform_to)

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
        self.wake(priority=Priority.INTERRUPT)

    def allow_interruption(self):
        self.run_until(self.env.current_time)
        return all(component.allow_interruption() for component in self.components)

    def check_interference(self, operation):
        raise NotImplementedError

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

    def wake(self, time=-1, priority=0):
        if self.state != self.STATE.WORKING or self.allow_interruption():
            self.activate(time, priority)

    def ready_for_new_task(self):
        if self.next_task:
            return False
        elif self.state == self.STATE.WORKING:
            return self.allow_interruption()
        else:
            return self.state != self.STATE.BLOCKING

    def submit_task(self, task, from_self=False):
        if isinstance(task, Request):
            task.equipment = self
        self.next_task = task
        if not from_self:
            if self.state == self.STATE.WORKING:
                if self.allow_interruption():
                    self.interrupt()
            elif self.state != self.STATE.BLOCKING:
                self.wake(priority=Priority.TASK_ARRIVAL)

    def query_new_task(self, time):
        if self.next_task is None:
            self.job_scheduler.schedule(time)

    def _wait(self, priority=Priority.FOREVER):
        if not self.next_task:
            op_or_req = self.job_scheduler.on_idle(self.time)
            if op_or_req is not None:
                self.submit_task(op_or_req, from_self=True)
                return self.time, priority
            else:
                return TIME_FOREVER, priority
        else:
            return self.next_task.time, priority

    def perform_op(self, time, op):
        op.commit(self.yard)
        with self.lock_state(self.STATE.WORKING):
            self.current_op = op
            self.yard.fire_probe('operation.start', op)
            op.state = op.STATE.RUNNING
            self.time = yield op.finish_time, Priority.OP_FINISH
            op.state = op.STATE.FINISHED
            op.finish_time = self.time
            self.current_op = None
            self.yard.fire_probe('operation.finish', op)
            # op.clean()

    def handle_request(self, request):
        request.start_or_resume(self.time)
        try:
            self.yard.fire_probe('request.start', request)
            for op in request.gen_op(self.time):
                if self.op_builder.build_and_check(self.time, op):
                    yield from self.perform_op(self.time, op)
                else:
                    op.state = op.STATE.CANCELLED
                    self.yard.fire_probe('operation.conflict', op)
                    raise ROREquipmentConflictError(op)
            self.yard.fire_probe('request.succeed', request)
        except ReqOpRejectionError as e:
            self.req_handler.on_reject(self.time, e)
            self.yard.fire_probe('request.rejected', request)
        request.finish_or_fail(self.time)

    def handle_operation(self, op):
        if self.op_builder.build_and_check(self.time, op):
            yield from self.perform_op(self.time, op)
        else:
            op.state = op.STATE.CANCELLED

    def _process(self):
        if self.next_task:
            op_or_req = self.next_task
            self.next_task = None
            if isinstance(op_or_req, Request):
                yield from self.handle_request(op_or_req)
            elif isinstance(op_or_req, Operation):
                yield from self.handle_operation(op_or_req)
            self.query_new_task(self.time)
        self.time = yield self.time, Priority.FOREVER

    def __getattr__(self, item):
        return self.attrs.get(item, None)

    def __repr__(self):
        return "<{}>{}.{} at {}".format(self.__class__.__name__, str(id(self.blocks[0]))[-4:], str(hash(self))[-4:],
                                        self.current_coord())
