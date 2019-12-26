from contextlib import contextmanager
from copy import copy
from enum import Enum, auto

from pesim import TIME_FOREVER, Process
from tcysim.framework.request import ReqStatus
from .priority import Priority
from .layout import EquipmentRangeLayout
from tcysim.utils import V3, TEU
from .request import Request
from .operation import OpBuilder


class Equipment(EquipmentRangeLayout, Process):
    class STATE(Enum):
        IDLE = auto()
        WORKING = auto()
        BLOCKING = auto()

    GRASP_TIME = 5
    RELEASE_TIME = 5

    OpBuilder = OpBuilder

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
        self.op_builder = self.OpBuilder(self)

    @contextmanager
    def save_state(self):
        for component in self.components:
            component.save_state()
        yield
        for component in self.components:
            component.restore_state()

    def coord(self):
        v = V3(0,0,0)
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
            v = V3(0,0,0)
            for component in self.components:
                v[component.axis] = component.loc
            return v
        else:
            return equipment.coord_g2l(self.coord())

    def attached_coord(self, teu=1):
        return self.coord().sub1(2, TEU.HEIGHT / 2)

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

    def check_interference(self, others, operation):
        raise NotImplementedError

    def nearby_equipments(self):
        for block in self.blocks:
            for equipment in block.equipments:
                if self is not equipment:
                    yield equipment

    @contextmanager
    def lock_status(self, s1, s2=STATE.IDLE):
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

    def submit_task(self, req_or_op):
        if isinstance(req_or_op, Request):
            req_or_op.equipment = self
        self.next_task = req_or_op
        if self.state == self.STATE.WORKING:
            if self.allow_interruption():
                self.interrupt()
        elif self.state != self.STATE.BLOCKING:
            self.wake(priority = Priority.TASK_ARRIVAL)

    def check_and_perform(self, op):
        self.op_builder.build(op)
        itf = True
        while itf:
            op.dry_run(self.time)
            itf, other, new_loc = self.check_interference(self.nearby_equipments(), op)
            print("Testing", self.time, itf, self.idx, self.state, op.op_type)
            print("{}<=>{}/{}".format(op.paths[self.gantry].min, op.paths[self.gantry].max, op.finish_time))
            if itf:
                print("ITF", self.time, self.idx, self.state, other.idx, other.state, id(other.current_op),
                      self.local_coord(), other.local_coord())
                new_loc = self.transform(other, new_loc)
                print("New loc", new_loc)
                if other.state == self.state.BLOCKING:
                    exit(2)
                if other.state == other.state.IDLE:
                    req = other.blocks[0].ReqHandler.AdjustRequest(self.time, other, new_loc)
                    req.link_signal("adjustment_started", self.wake, priority=Priority.INTERFERENCE_RELEASE)
                    self.yard.tmgr.submit_request(self.time, req)
                    with self.lock_status(self.STATE.BLOCKING):
                        # self.time = yield TIME_FOREVER, Priority.FOREVER
                        yield TIME_FOREVER, Priority.FOREVER
                        self.yard.run_until(self.time)
                elif other.state == other.state.WORKING:
                    op.request.send_back(self.time, op)
                    break
            else:
                op.commit(self.yard)
                # if op.op_type == self.OpBuilder.OpType.ADJUST:
                #     print(self.time, id(op), op.finish_time)
                with self.lock_status(self.STATE.WORKING):
                    self.current_op = op
                    # self.time = yield op.finish_time, Priority.OP_FINISH
                    yield op.finish_time, Priority.OP_FINISH
                    # print("<>", self.idx, self.time, itf)
                    self.yard.run_until(self.time)
                    self.current_op = None

    def on_idle(self, time):
        # print(self.idx, "is idle", time, self.ready_for_new_task(), self.next_task, self.state, self.allow_interruption())
        # print(self.gantry.pending_motions)
        # print(self.trolley.pending_motions)
        # print(self.hoist.pending_motions)
        self.yard.tmgr.schedule(time)

    def is_idle(self):
        return not self.next_task

    def _wait(self, priority=Priority.FOREVER):
        if not self.next_task:
            return TIME_FOREVER, priority
        else:
            return self.next_task.time, priority

    def _process(self):
        self.yard.run_until(self.time)
        req_or_op = self.next_task
        self.next_task = None
        print("\n[{}/Start]".format(self.idx), self.time, req_or_op, id(req_or_op), self.local_coord())
        if isinstance(req_or_op, Request):
            req_or_op.start(self.time)
            for op in req_or_op.block.handle_request(self.time, req_or_op):
                for item in self.check_and_perform(op):
                    self.time = yield item
                if req_or_op.status == ReqStatus.SENTBACK:
                    self.yard.tmgr.send_back(req_or_op)
                    break
            req_or_op.finish(self.time)
        else:
            for item in self.check_and_perform(req_or_op):
                self.time = yield item
        print("[{}/Finish]".format(self.idx), self.time, self.local_coord())
        if self.is_idle():
            self.on_idle(self.time)

    def __getattr__(self, item):
        return self.attrs.get(item, None)