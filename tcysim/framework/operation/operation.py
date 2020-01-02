from contextlib import contextmanager
from copy import copy

from ..callback import CallBack
from .step import CallBackStep, EmptyStep, MoverStep
from tcysim.utils import Paths, V3


class Operation:
    def __init__(self, type, request, locking_pos=(), **attrs):
        self.op_type = type
        self.start_time = -1
        self.finish_time = -1
        self.request = request
        self.equipment = request.equipment
        self.step = None
        self.paths = {}
        self.__interruption_flag = False
        self.locking_positions = list(locking_pos)
        self.__dict__.update(attrs)

    def add_lock(self, pos):
        self.locking_positions.append(pos)

    @property
    def TYPE(self):
        return self.equipment.op_builder.OpType

    def mark_loc(self, component, time, loc):
        if component in self.paths:
            self.paths[component].append(time, loc)

    def commit(self, yard):
        self.step.commit(yard)

    def dry_run(self, start_time):
        equipment = self.equipment
        for component in equipment.components:
            if component.may_interfere:
                paths = Paths(64)
                paths.append(start_time, equipment.local_coord()[component.axis])
                self.paths[component] = paths
        self.start_time = start_time
        with equipment.save_state():
            self.finish_time = self.step(self, start_time)

    def add(self, step):
        if not self.step:
            self.step = step
        else:
            self.step = self.step >> step

    def extend(self, steps):
        for step in steps:
            self.add(step)

    def emit_signal(self, name):
        return CallBackStep(self.request.signals[name])

    def wait(self, time):
        return EmptyStep(self.equipment.components[0], time)

    def move(self, component, src_loc, dst_loc, mode="default"):
        if isinstance(src_loc, V3):
            src_loc = src_loc[component.axis]
        if isinstance(dst_loc, V3):
            dst_loc = dst_loc[component.axis]
        # if src_loc == dst_loc:
        #     return NullStep()
        return MoverStep(component, src_loc, dst_loc, self.__interruption_flag, mode=mode)

    @contextmanager
    def allow_interruption(self, equipment):
        self.__interruption_flag = True
        self.add(CallBackStep(CallBack(equipment.on_idle)))
        yield
        self.__interruption_flag = False

    def __repr__(self):
        return "<OP/{}>{}".format(self.op_type.name, str(hash(self))[:4])
