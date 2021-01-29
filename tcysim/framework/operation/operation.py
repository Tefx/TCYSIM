from abc import ABC, abstractmethod
from contextlib import contextmanager
from enum import Enum, auto, IntEnum
from typing import Type
import heapq

from .step import CallBackStep, EmptyStep, GraspStep, ReleaseStep, MoverStep, ProbeStep, StepWorkflow
from ..event_reason import EventReason
from ..request import RequestBase
from ..callback import CallBack
from tcysim.utils import Paths, V3


class OpType(Enum):
    pass


class OpState(IntEnum):
    INIT = auto()
    RUNNING = auto()
    FINISHED = auto()
    CANCELLED = auto()



class OperationABC(ABC):
    STATE: Type[IntEnum] = OpState
    gid = 0

    def __init__(self, request_or_equipment, **attrs):
        if isinstance(request_or_equipment, RequestBase):
            self.request = request_or_equipment
            self.equipment = request_or_equipment.equipment
        else:
            self.request = None
            self.equipment = request_or_equipment
        self.state = self.STATE.INIT
        self.start_time = -1
        self.finish_time = -1
        self.attach_time = -1
        self.detach_time = -1
        self.attach_pos = None
        self.detach_pos = None
        self.interrupted = False
        self.id = OperationABC.gid
        OperationABC.gid += 1
        self.__dict__.update(attrs)

    def build_and_check(self, time, builder):
        return True

    @abstractmethod
    def perform(self, yard):
        with self.running_context():
            pass

    def cancel(self, yard):
        self.state = self.STATE.CANCELLED

    def clean(self):
        pass

    @contextmanager
    def running_context(self):
        self.start_time = self.equipment.time
        self.state = self.STATE.RUNNING
        yield
        self.state = self.STATE.FINISHED
        self.finish_time = self.equipment.time


class OperationBase(OperationABC):
    TYPE: Type[Enum] = NotImplementedError

    def __init__(self, type, request_or_equipment, box=None, **attrs):
        super(OperationBase, self).__init__(request_or_equipment, **attrs)
        self.box = box
        self.op_type = type
        self.workflow = StepWorkflow()
        self.interruption_flag = False
        self._pps = {}
        self.paths = {}
        self.start_coord = None

    def check_interference(self):
        itf, other, new_loc = self.equipment.check_interference(self)
        if itf:
            self.itf_other = other
            self.itf_loc = new_loc
        return not itf

    def build_and_check(self, time, builder):
        for step in builder.dispatch(self.op_type.name, "_", self):
            self.workflow.add(step)
        self.dry_run(time)
        return self.check_interference()

    def perform(self, yard):
        self.workflow.commit(yard, self)
        with self.running_context():
            self.start_coord = self.equipment.current_coord()
            yield self.finish_time, EventReason.OP_FINISHED

    def clean(self):
        self._pps = None
        self.workflow = None
        self.paths = None

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
            self.finish_time = self.workflow.dry_run(self, self.start_time)
            self.record_path_points()

    def extend(self, steps):
        for step in steps:
            self.workflow.add(step)

    def emit_signal(self, name):
        return CallBackStep(self.request.signals[name])

    def emit_callback(self, func, *args, **kwargs):
        return CallBackStep(CallBack(func, *args, **kwargs))

    def fire_probe(self, probe_name, *args, probe_reason=EventReason.PROBE_ACTION, **kwargs):
        return ProbeStep(probe_name, args, kwargs, probe_reason)

    def wait(self, time):
        return EmptyStep(self.equipment.components[0], time)

    # def sync(self):
    #     return SyncStep(self.request)

    def grasp(self, time, pos, sync=False):
        return GraspStep(self.equipment.components[0], time, pos, sync)

    def release(self, time, pos, sync=False):
        return ReleaseStep(self.equipment.components[0], time, pos, sync)

    def grasp2(self, time, sync=False):
        equipment = self.equipment
        pos = equipment.current_coord() + equipment.BoxEquipmentDelta
        return GraspStep(equipment.components[0], time, pos, sync)

    def release2(self, time, sync=False):
        equipment = self.equipment
        pos = equipment.current_coord() + equipment.BoxEquipmentDelta
        return ReleaseStep(equipment.components[0], time, pos, sync)

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
            cbs = CallBackStep(CallBack(equipment.query_new_task))
            self.workflow.add(cbs)
        yield
        self.interruption_flag = False

    @contextmanager
    def handle_interruption(self, allow, query_task_before_perform=True):
        if allow:
            self.interruption_flag = True
            if query_task_before_perform:
                cbs = CallBackStep(CallBack(self.equipment.query_new_task))
                self.workflow.add(cbs)
        yield
        if allow:
            self.interruption_flag = False

    def __repr__(self):
        return "<OP/{}>{}".format(self.op_type.name, str(hash(self))[-4:0])

    def dump(self):
        return self.workflow.dump(self.start_time)

    # @property
    # def distance(self):
    #     return self.workflow.distance()
    #
    # @property
    # def moving_time(self):
    #     return self.workflow.moving_time()

    def iter_component_moves(self):
        res_d = {}
        res_t = {}
        for mover, mode, dis, time in self.workflow.iter_component_moves(self.equipment.time):
            key = mover, mode
            if key not in res_d:
                res_d[key] = dis
                res_t[key]= time
            else:
                res_d[key] += dis
                res_t[key] += time
        for key in res_d.keys():
            mover, mode = key
            yield mover, mode, res_d[key], res_t[key]


class BlockingOperationBase(OperationABC):
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.op_type = cls.__name__
