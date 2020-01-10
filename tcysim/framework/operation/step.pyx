import heapq
from math import inf

from ..motion.motion cimport Motion
from ..motion.mover cimport Mover

cimport cython

@cython.freelist(10000)
cdef class StepBase:
    cdef StepBase pred
    cdef readonly float start_time
    cdef readonly float finish_time
    cdef float next_time
    cdef bint executed
    cdef bint committed

    def __cinit__(StepBase self):
        self.pred = None
        self.start_time = 0
        self.finish_time = 0
        self.next_time = 0
        self.executed = False
        self.committed = False

    def reset(StepBase self):
        if self.executed:
            self.executed = False
            self.committed = False
            if self.pred and self.pred.executed:
                self.pred.reset()

    cdef cal_start_time(StepBase self, op, float est):
        if not self.executed:
            self.start_time = est
            if self.pred and self.pred.next_time > est:
                self.start_time = self.pred.next_time
        return self.start_time

    cdef cal_pred(StepBase self, op, float est):
        if self.pred:
            self.pred.execute(op, est)

    def __call__(StepBase self, op, float est):
        return self.execute(op, est)

    cdef execute(StepBase self, op, float est):
        raise NotImplementedError

    def commit(StepBase self, yard):
        self.committed = True

    def __and__(StepBase self, StepBase other):
        cdef AndStep astep
        if isinstance(other, AndStep):
            astep = other
            return astep & self
        else:
            return AndStep(self, other)

    def __or__(StepBase self, StepBase other):
        cdef OrStep ostep
        if isinstance(other, OrStep):
            ostep = other
            return ostep | self
        else:
            return OrStep(self, other)

    cdef add_pred(StepBase self, StepBase other):
        if self.pred:
            self.pred = self.pred & other
        else:
            self.pred = other

    def __ilshift__(StepBase self, StepBase other):
        self.add_pred(other)
        return self

    def __lt__(StepBase self, StepBase other):
        return self.start_time < other.start_time

    def __repr__(StepBase self):
        return "<{}|{}>".format(self.__class__.__name__, str(id(self)))

cdef class EmptyStep(StepBase):
    cdef Mover mover
    cdef float time
    cdef Motion motion

    def __init__(EmptyStep self, Mover mover, float time):
        self.mover = mover
        self.time = time
        self.motion = None

    cdef execute(EmptyStep self, op, float est):
        if not self.executed:
            self.cal_pred(op, est)
            self.cal_start_time(op, est)
            self.finish_time = self.start_time + self.time
            self.next_time = self.finish_time
            self.motion = Motion(self.start_time, self.time, 0, 0, allow_interruption=False)
        self.executed = True

    def commit(EmptyStep self, yard):
        cdef Mover mover
        if not self.committed:
            mover = self.mover
            mover.commit_motions((self.motion,))
        self.committed = True

cdef class CallBackStep(StepBase):
    cdef object callback

    def __init__(CallBackStep self, callback):
        self.callback = callback

    cdef execute(CallBackStep self, op, float est):
        if not self.executed:
            self.cal_pred(op, est)
            self.cal_start_time(op, est)
            self.finish_time = self.start_time
            self.next_time = self.finish_time
            self.callback.time = self.start_time
        self.executed = True

    def commit(CallBackStep self, yard):
        if not self.committed:
            yard.cmgr.add(self.callback)
        self.committed = True

cdef class MoverStep(StepBase):
    cdef Mover mover
    cdef float src_loc
    cdef float dst_loc
    cdef list motions
    cdef object mode
    cdef bint allow_interruption

    def __init__(Mover self, Mover mover, float src, float dst, bint allow_interruption=False, mode="default"):
        self.mover = mover
        self.src_loc = src
        self.dst_loc = dst
        self.motions = None
        self.mode = mode
        self.allow_interruption = allow_interruption

    cdef execute(MoverStep self, op, float est):
        cdef Mover mover
        cdef Motion motion
        cdef float loc
        cdef float rt

        if not self.executed:
            self.cal_pred(op, est)
            self.cal_start_time(op, est)

            mover = self.mover
            op.mark_loc(self.mover, self.start_time, self.src_loc)
            rt, self.motions = mover.create_motions(
                self.start_time, self.dst_loc - self.src_loc,
                self.allow_interruption, self.mode
                )

            loc = self.src_loc
            for motion in self.motions:
                loc += motion.displacement
                op.mark_loc(self.mover, motion.finish_time, loc)

            self.finish_time = self.start_time + rt
            self.next_time = self.finish_time
        self.executed = True

    def commit(Mover self, yard):
        cdef Mover mover
        if not self.committed:
            mover = self.mover
            mover.commit_motions(self.motions)
        self.committed = True

    def __repr__(self):
        return "[{}]Move<{:.2f}=>{:.2f}|{:.2f}/{:.2f}>".format(self.mover.axis, self.src_loc, self.dst_loc, self.start_time, self.finish_time)

cdef class CompoundStep(StepBase):
    cdef list steps

    def __init__(CompoundStep self, *steps):
        self.steps = list(steps)

cdef class AndStep(CompoundStep):
    cdef execute(AndStep self, op, float est):
        cdef StepBase step

        if not self.executed:
            self.cal_pred(op, est)
            self.cal_start_time(op, est)
            self.finish_time = 0
            self.next_time = 0
            for step in self.steps:
                step.execute(op, est)
                if step.finish_time > self.finish_time:
                    self.finish_time = step.finish_time
                if step.next_time > self.next_time:
                    self.next_time = step.next_time
        self.executed = True

    def __and__(AndStep self, StepBase other):
        cdef AndStep astep
        if isinstance(other, AndStep):
            astep = other
            self.steps.extend(astep.steps)
        else:
            self.steps.append(other)
        return self

    def __repr__(AndStep self):
        return "<{}>[{}]".format(self.__class__.__name__, " & ".join(repr(s) for s in self.steps))

cdef class OrStep(CompoundStep):
    cdef execute(OrStep self, op, float est):
        cdef StepBase step

        if not self.executed:
            self.cal_pred(op, est)
            self.cal_start_time(op, est)
            self.finish_time = 0
            self.next_time = inf
            for step in self.steps:
                step.execute(op, est)
                if step.finish_time > self.finish_time:
                    self.finish_time = step.finish_time
                if step.next_time > self.next_time:
                    self.next_time = step.next_time
        self.executed = True

    def __or__(OrStep self, StepBase other):
        cdef OrStep ostep
        if isinstance(other, OrStep):
            ostep = other
            self.steps.extend(ostep.steps)
        else:
            self.steps.append(other)
        return self

    def __repr__(OrStep self):
        return "<{}|{}>[{}]".format(self.__class__.__name__, str(id(self)),
                                    " | ".join(repr(s) for s in self.steps))


cdef class StepWorkflow:
    cdef list steps
    cdef list sorted_steps
    cdef StepBase last_step
    cdef readonly float finish_time

    def __cinit__(self):
        self.steps = []
        self.last_step = None
        self.finish_time = 0

    def add(self, step_or_steps):
        cdef StepBase step
        if isinstance(step_or_steps, StepBase):
            step = step_or_steps
            self.steps.append(step)
            if self.last_step:
                step.add_pred(self.last_step)
            self.last_step = step
        else:
            for step in step_or_steps:
                self.steps.append(step)
                if self.last_step:
                    step.add_pred(self.last_step)
            self.last_step = AndStep(*step_or_steps)

    def reset(self):
        for step in self.steps:
            step.reset()

    def __call__(self, op, float st):
        cdef StepBase step
        self.sorted_steps = []
        self.finish_time = 0
        for step in self.steps:
            step.execute(op, st)
            heapq.heappush(self.sorted_steps, step)
            if self.finish_time < step.finish_time:
                self.finish_time = step.finish_time
        # print(self.steps)
        # print(self.sorted_steps)
        return self.finish_time

    def commit(self, yard):
        cdef StepBase step
        while self.sorted_steps:
            step = heapq.heappop(self.sorted_steps)
            step.commit(yard)


