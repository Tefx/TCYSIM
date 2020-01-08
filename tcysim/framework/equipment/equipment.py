from contextlib import contextmanager
from copy import copy
from enum import Enum, auto

from pesim import TIME_FOREVER, Process
from ..exception.handling import ReqOpRejectionError, ROREquipmentConflictError
from ..operation import Operation
from ..priority import Priority
from ..layout import EquipmentRangeLayout
from tcysim.utils import V3
from ..request import Request
from .req_handler import ReqHandler
from .op_builder import OpBuilder
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
        self.current_op = None
        self.state = self.STATE.IDLE
        self.next_task = None
        self.components = [copy(item) for item in components]
        self.set_coord(init_offset, glob=False)
        self.attrs = copy(attrs)
        self.req_handler = self.ReqHandler(self)
        self.op_builder = self.OpBuilder(self)
        self.job_scheduler = self.JobScheduler(self)

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

    def coord(self):
        v = V3(0, 0, 0)
        for component in self.components:
            v[component.axis] = component.loc
        return self.coord_l2g(v)

    def set_coord(self, v, glob=True):
        if glob:
            v = self.coord_g2l(v)
        for component in self.components:
            component.loc = v[component.axis]

    def local_coord(self, equipment=None):
        if equipment is None:
            v = V3(0, 0, 0)
            for component in self.components:
                v[component.axis] = component.loc
            return v
        else:
            return equipment.coord_g2l(self.coord())

    def coord_to_box(self):
        return self.coord()

    def coord_from_box(self, coord):
        return coord

    def coord_ready_for_box(self, coord):
        return coord

    def assign_block(self, block):
        self.blocks.append(block)

    def run_until(self, time):
        for component in self.components:
            component.run_until(time)

    def interrupt(self):
        for component in self.components:
            component.interrupt()
        self.wake(priority=Priority.INTERRUPT)

    def allow_interruption(self):
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

    def submit_task(self, request):
        if isinstance(request, Request):
            request.equipment = self
        self.next_task = request
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
            op = self.job_scheduler.on_idle(self.time)
            if op is not None:
                self.next_task = op
                return self.time, priority
            else:
                return TIME_FOREVER, priority
        else:
            return self.next_task.time, priority

    def perform_op(self, time, op):
        op.commit(self.yard)
        with self.lock_state(self.STATE.WORKING):
            self.current_op = op
            self.time = yield op.finish_time, Priority.OP_FINISH
            self.current_op = None

    def handle_request(self, request):
        print("[{:.2f}]<Request/Equipment {}>".format(self.time, self.idx), request, self.local_coord(),
              getattr(request, "box", None))
        request.start_or_resume(self.time)
        try:
            for op in request.gen_op(self.time):
                if self.op_builder.build_and_check(self.time, op):
                    yield from self.perform_op(self.time, op)
                else:
                    raise ROREquipmentConflictError(op)
        except ReqOpRejectionError as e:
            self.req_handler.on_reject(self.time, e)
        request.finish_or_fail(self.time)
        print("[{:.2f}]<Request/Equipment {}>".format(self.time, self.idx), request, self.local_coord(),
              getattr(request, "box", None))

    def handle_operation(self, op):
        print("[{:.2f}]<Operation/Start {}>".format(self.time, self.idx), op, self.local_coord())
        if self.op_builder.build_and_check(self.time, op):
            yield from self.perform_op(self.time, op)
        print("[{:.2f}]<Operation/FinishOrFail {}>".format(self.time, self.idx), op, self.local_coord())

    def _process(self):
        op_or_req = self.next_task
        self.next_task = None
        if isinstance(op_or_req, Request):
            yield from self.handle_request(op_or_req)
        elif isinstance(op_or_req, Operation):
            yield from self.handle_operation(op_or_req)
        self.query_new_task(self.time)
        self.time = yield self.time, Priority.FOREVER

    def adjust_is_necessary(self, other, dst_loc):
        return (other.local_coord() - dst_loc).dot_product(self.local_coord() - dst_loc) >= 0

    def __getattr__(self, item):
        return self.attrs.get(item, None)

    def __repr__(self):
        return "<{}>{} at {}".format(self.__class__.__name__, str(hash(self))[:4], self.local_coord())
