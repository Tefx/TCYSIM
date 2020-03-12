import heapq
from libc.float cimport DBL_MAX

from tcysim.utils.math cimport feq
from ..motion.motion cimport Motion
from ..motion.mover cimport Mover

from cython cimport freelist
from cpython cimport PyObject

@freelist(1024)
cdef class StepBase:
    cdef StepBase pred
    cdef readonly double start_time
    cdef readonly double finish_time
    cdef double next_time
    cdef bint executed
    cdef bint committed

    def __cinit__(StepBase self):
        self.pred = None
        self.start_time = 0
        self.finish_time = 0
        self.next_time = 0
        self.executed = False
        self.committed = False

    cdef void reset(StepBase self):
        if self.executed:
            self.executed = False
            self.committed = False
            if self.pred is not None and self.pred.executed:
                self.pred.reset()

    cdef double cal_start_time(StepBase self, op, double est):
        if not self.executed:
            self.start_time = est
            if self.pred is not None and self.pred.next_time > est:
                self.start_time = self.pred.next_time
        return self.start_time

    cdef void cal_pred(StepBase self, op, double est):
        if self.pred is not None:
            self.pred.execute(op, est)

    def __call__(StepBase self, op, double est):
        return self.execute(op, est)

    cdef void execute(StepBase self, op, double est):
        raise NotImplementedError

    cdef void commit(self, yard):
        self.committed = True

    cdef StepBase and_c(StepBase self, StepBase other):
        if isinstance(other, AndStep):
            (<AndStep> other)._and(self)
            return other
        else:
            return AndStep(self, other)

    cdef StepBase or_c(StepBase self, StepBase other):
        if isinstance(other, OrStep):
            (<OrStep> other)._or(self)
            return other
        else:
            return OrStep(self, other)

    def __and__(StepBase self, StepBase other):
        return self.and_c(other)

    def __or__(StepBase self, StepBase other):
        return self.or_c(other)

    cdef void add_pred(StepBase self, StepBase other):
        if self.pred is not None:
            self.pred = self.pred.and_c(other)
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
    cdef double time
    cdef Motion motion

    def __init__(EmptyStep self, Mover mover, double time):
        self.mover = mover
        self.time = time
        self.motion = None

    cdef void execute(EmptyStep self, op, double est):
        if not self.executed:
            self.cal_pred(op, est)
            self.cal_start_time(op, est)
            self.finish_time = self.start_time + self.time
            self.next_time = self.finish_time
            self.motion = Motion(self.start_time, self.time, 0, 0, allow_interruption=False)
        self.executed = True

    cdef void commit(self, yard):
        if not self.committed:
            (<EmptyStep> self).mover.commit_motions(((<EmptyStep> self).motion,))
        self.committed = True

cdef class SyncStep(StepBase):
    cdef object req

    def __init__(self, object req):
        self.req = req

    cdef void execute(SyncStep self, op, double est):
        if not self.executed:
            self.cal_pred(op, est)
            self.cal_start_time(op, est)
            self.finish_time = self.start_time
            self.next_time = self.finish_time
        self.executed = True

    cdef void commit(self, yard):
        if not self.committed:
            self.req.sync_time = self.finish_time
        self.committed = True

cdef class CallBackStep(StepBase):
    cdef object callback

    def __init__(CallBackStep self, object callback):
        self.callback = callback

    cdef void execute(CallBackStep self, op, double est):
        if not self.executed:
            self.cal_pred(op, est)
            self.cal_start_time(op, est)
            self.finish_time = self.start_time
            self.next_time = self.finish_time
            self.callback.time = self.start_time
        self.executed = True

    cdef void commit(self, yard):
        if not self.committed:
            yard.cmgr.add(self.callback)
        self.committed = True

cdef class MoverStep(StepBase):
    cdef Mover mover
    cdef double src_loc
    cdef double dst_loc
    cdef list motions
    cdef str mode
    cdef bint allow_interruption
    cdef double start_v

    def __init__(Mover self, Mover mover, double src, double dst, bint allow_interruption=False, str mode="default"):
        self.mover = mover
        self.src_loc = src
        self.dst_loc = dst
        self.motions = None
        self.mode = mode
        self.allow_interruption = allow_interruption

    cdef void execute(MoverStep self, op, double est):
        cdef double loc
        cdef double rt

        if not self.executed:
            self.cal_pred(op, est)
            self.cal_start_time(op, est)

            self.start_v = self.mover.curr_v

            op.mark_loc(self.mover, self.start_time, self.src_loc)
            if not feq(self.src_loc, self.dst_loc):
                rt, self.motions = self.mover.create_motions(
                    self.start_time, self.dst_loc - self.src_loc,
                    self.allow_interruption, self.mode
                    )
            else:
                rt = 0
                self.motions = []

            loc = self.src_loc
            for motion in self.motions:
                loc += (<Motion> motion).displacement
                op.mark_loc(self.mover, (<Motion> motion).finish_time, loc)

            self.finish_time = self.start_time + rt
            self.next_time = self.finish_time
        self.executed = True

    cdef void commit(self, yard):
        if not self.committed and self.start_time != self.finish_time:
            self.mover.commit_motions(self.motions)
        self.committed = True

    cdef list reduce(self):
        cdef Motion m
        cdef list seq = [self.mover.axis, self.mode, self.start_time, self.start_v]
        for m in self.motions:
            seq.append(<int> (m.a * 1000))
            seq.append(<int> (m._orig_timespan * 1000))
        return seq

    def __repr__(self):
        return "[{}]Move<{:.2f}=>{:.2f}|{:.2f}/{:.2f}>".format(self.mover.axis, self.src_loc, self.dst_loc,
                                                               self.start_time, self.finish_time)

cdef class CompoundStep(StepBase):
    cdef list steps

    def __init__(CompoundStep self, *steps):
        self.steps = list(steps)

cdef class AndStep(CompoundStep):
    cdef void execute(AndStep self, op, double est):
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

    cdef void _and(AndStep self, StepBase other):
        if isinstance(other, AndStep):
            self.steps.extend((<AndStep> other).steps)
        else:
            self.steps.append(other)

    def __and__(AndStep self, StepBase other):
        self._and(other)
        return self

    def __repr__(AndStep self):
        return "<{}>[{}]".format(self.__class__.__name__, " & ".join(repr(s) for s in self.steps))

cdef class OrStep(CompoundStep):
    cdef void execute(OrStep self, op, double est):
        cdef StepBase step

        if not self.executed:
            self.cal_pred(op, est)
            self.cal_start_time(op, est)
            self.finish_time = 0
            self.next_time = DBL_MAX
            for step in self.steps:
                step.execute(op, est)
                if step.finish_time > self.finish_time:
                    self.finish_time = step.finish_time
                if step.next_time < self.next_time:
                    self.next_time = step.next_time
        self.executed = True

    cdef void _or(OrStep self, StepBase other):
        if isinstance(other, OrStep):
            self.steps.extend((<OrStep> other).steps)
        else:
            self.steps.append(other)

    def __or__(OrStep self, StepBase other):
        self._or(other)
        return self

    def __repr__(OrStep self):
        return "<{}|{}>[{}]".format(self.__class__.__name__, str(id(self)),
                                    " | ".join(repr(s) for s in self.steps))

cdef class StepWorkflow:
    cdef list steps
    cdef list sorted_steps
    cdef StepBase last_step
    cdef double start_time, finish_time
    cdef readonly sync_time

    def __cinit__(self):
        self.steps = []
        self.last_step = None
        self.finish_time = 0
        self.sync_time = -1

    def add(self, step_or_steps):
        cdef StepBase step
        if isinstance(step_or_steps, StepBase):
            self.steps.append(step_or_steps)
            if self.last_step:
                (<StepBase> step_or_steps).add_pred(self.last_step)
            self.last_step = step_or_steps
        else:
            for step in step_or_steps:
                self.steps.append(step)
                if self.last_step:
                    step.add_pred(self.last_step)
            self.last_step = AndStep(*step_or_steps)

    def reset(self):
        cdef StepBase step
        for step in self.steps:
            step.reset()

    def dry_run(self, op, double st):
        cdef StepBase step
        self.start_time = 0
        self.finish_time = 0
        self.sorted_steps = []
        for step in self.steps:
            step.execute(op, st)
            heapq.heappush(self.sorted_steps, step)
            if self.finish_time < step.finish_time:
                self.finish_time = step.finish_time
        return self.finish_time

    def commit(self, yard):
        cdef StepBase step
        while self.sorted_steps:
            step = heapq.heappop(self.sorted_steps)
            step.commit(yard)

    def dump(self, packer):
        cdef StepBase step
        cdef list res = []
        for step in self.steps:
            if isinstance(step, MoverStep) and \
                    (<MoverStep> step).start_time != (<MoverStep> step).finish_time:
                res.append((<MoverStep> step).reduce())
        return packer.pack(res)
