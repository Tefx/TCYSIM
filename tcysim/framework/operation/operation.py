from contextlib import contextmanager

from .step import CallBackStep, EmptyStep, MoverStep, AndStep
from ..request import Request
from ..callback import CallBack
from tcysim.utils import Paths, V3


class Operation:
    def __init__(self, type, request_or_equipment, locking_pos=(), **attrs):
        self.op_type = type
        self.start_time = -1
        self.finish_time = -1
        if isinstance(request_or_equipment, Request):
            self.request = request_or_equipment
            self.equipment = request_or_equipment.equipment
        else:
            self.request = None
            self.equipment = request_or_equipment
        self.steps = set()
        self.last_step = None
        self.paths = {}
        self.__interruption_flag = False
        self.locking_positions = list(locking_pos)
        self.__dict__.update(attrs)
        self._pps = {}

    def add_lock(self, pos):
        self.locking_positions.append(pos)

    @property
    def TYPE(self):
        return self.equipment.op_builder.OpType

    def mark_loc(self, component, time, loc):
        if component in self.paths:
            self._pps[component].append((time, loc))

    def record_path_points(self):
        for component, path in self.paths.items():
            self._pps[component].sort()
            for point in self._pps[component]:
                path.append(*point)

    def commit(self, yard):
        for step in self.steps:
            step.commit(yard)

    def dry_run(self, start_time):
        for step in self.steps:
            step.reset()
        equipment = self.equipment
        for component in equipment.components:
            if component.may_interfere:
                paths = Paths(64)
                paths.append(start_time, equipment.current_coord()[component.axis])
                self.paths[component] = paths
                self._pps[component] = []
        self.start_time = start_time
        with equipment.save_state():
            for step in self.steps:
                step(self, self.start_time)
            self.finish_time = max(step.finish_time for step in self.steps)
        self.steps = sorted(self.steps, key=lambda x: x.start_time)
        self.record_path_points()

        # for step in self.steps:
        #     print(step, step.pred, step.start_time, step.finish_time, step.next_time)

    def add(self, step):
        if isinstance(step, tuple):
            steps = step
        else:
            steps = (step,)
        for step in steps:
            if self.last_step:
                step <<= self.last_step
            self.steps.add(step)
        self.last_step = AndStep(*steps) if len(steps) > 1 else steps[0]

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
    def allow_interruption(self, equipment, query_task_before_perform=True):
        self.__interruption_flag = True
        if query_task_before_perform:
            self.add(CallBackStep(CallBack(equipment.query_new_task)))
        yield
        self.__interruption_flag = False

    def __repr__(self):
        return "<OP/{}>{}".format(self.op_type.name, str(hash(self))[:4])
