from contextlib import contextmanager
from enum import auto, IntEnum

from .step import CallBackStep, EmptyStep, MoverStep, AndStep, StepWorkflow
from ..request import Request
from ..callback import CallBack
from tcysim.utils import Paths, V3

import heapq


class OpState(IntEnum):
    INIT = auto()
    RUNNING = auto()
    FINISHED = auto()
    CANCELLED = auto()


class Operation:
    STATE = OpState

    def __init__(self, type, request_or_equipment, locking_pos=(), **attrs):
        self.op_type = type
        self.state = OpState.INIT
        self.start_time = -1
        self.finish_time = -1
        if isinstance(request_or_equipment, Request):
            self.request = request_or_equipment
            self.equipment = request_or_equipment.equipment
        else:
            self.request = None
            self.equipment = request_or_equipment
        self._pps = {}
        self.workflow = StepWorkflow()
        self.paths = {}
        self.interruption_flag = False
        self.locking_positions = list(locking_pos)
        self.__dict__.update(attrs)

    def clean(self):
        self._pps = None
        self.workflow = None
        self.paths = None
        self.locking_positions = None

    def add_lock(self, pos):
        self.locking_positions.append(pos)

    @property
    def TYPE(self):
        return self.equipment.op_builder.OpType

    @property
    def operation_time(self):
        return self.finish_time - self.start_time

    def mark_loc(self, component, time, loc):
        if component in self.paths:
            heapq.heappush(self._pps[component], (time, loc))

    def record_path_points(self):
        for component, path in self.paths.items():
            pps = self._pps[component]
            while pps:
                path.append(*heapq.heappop(pps))

    def commit(self, yard):
        self.workflow.commit(yard)

    def dry_run(self, start_time):
        self.workflow.reset()
        equipment = self.equipment
        for component in equipment.components:
            if component.may_interfere:
                paths = Paths(64)
                paths.append(start_time, equipment.current_coord()[component.axis])
                self.paths[component] = paths
                self._pps[component] = []
        self.start_time = start_time
        with equipment.save_state():
            self.finish_time = self.workflow(self, self.start_time)
            self.record_path_points()

    def extend(self, steps):
        for step in steps:
            self.workflow.add(step)

    def emit_signal(self, name):
        return CallBackStep(self.request.signals[name])

    def wait(self, time):
        return EmptyStep(self.equipment.components[0], time)

    def move(self, component, src_loc, dst_loc, mode="default"):
        if isinstance(src_loc, V3):
            src_loc = src_loc[component.axis]
        if isinstance(dst_loc, V3):
            dst_loc = dst_loc[component.axis]
        return MoverStep(component, src_loc, dst_loc, self.interruption_flag, mode=mode)

    @contextmanager
    def allow_interruption(self, equipment, query_task_before_perform=True):
        self.interruption_flag = True
        if query_task_before_perform:
            cbs = CallBackStep(self.workflow, CallBack(equipment.query_new_task))
            self.workflow.add(cbs)
        yield
        self.interruption_flag = False

    def __repr__(self):
        return "<OP/{}>{}".format(self.op_type.name, str(hash(self))[-4:0])
