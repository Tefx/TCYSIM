from math import inf

from ..motion import Motion


class StepBase:
    def __init__(self):
        self.pred = None
        self.start_time = None
        self.finish_time = None
        self.next_time = None
        self.executed = False
        self.committed = False

    def reset(self):
        self.executed = False
        self.committed = False

    def cal_start_time(self, op, est):
        if not self.executed:
            self.start_time = est
            if self.pred:
                self.start_time = max(self.pred.next_time, est)
        return self.start_time

    def cal_pred(self, op, est):
        if self.pred:
            self.pred(op, est)

    def __call__(self, op, est):
        raise NotImplementedError

    def commit(self, yard):
        self.committed = True

    def __and__(self, other):
        if isinstance(other, AndStep):
            return other & self
        else:
            return AndStep(self, other)

    def __or__(self, other):
        if isinstance(other, OrStep):
            return other | self
        else:
            return OrStep(self, other)

    def __ilshift__(self, other):
        if self.pred:
            self.pred = self.pred & other
        else:
            self.pred = other
        return self

    def __repr__(self):
        return "<{}|{}>".format(self.__class__.__name__, str(id(self))[-4:])


class NullStep(StepBase):
    def __init__(self):
        super(NullStep, self).__init__()


class EmptyStep(StepBase):
    def __init__(self, mover, time):
        super(EmptyStep, self).__init__()
        self.mover = mover
        self.time = time
        self.motion = None

    def __call__(self, op, est):
        if not self.executed:
            self.cal_pred(op, est)
            self.cal_start_time(op, est)
            self.finish_time = self.start_time + self.time
            self.next_time = self.finish_time
            self.motion = Motion(self.start_time, self.time, 0, 0, allow_interruption=False)
        self.executed = True

    def commit(self, yard):
        if not self.committed:
            self.mover.commit_motions((self.motion,))
        self.committed = True


class CallBackStep(StepBase):
    def __init__(self, callback):
        super(CallBackStep, self).__init__()
        self.callback = callback

    def __call__(self, op, est):
        if not self.executed:
            self.cal_pred(op, est)
            self.cal_start_time(op, est)
            self.finish_time = self.start_time
            self.next_time = self.finish_time
            self.callback.time = self.start_time
        self.executed = True

    def commit(self, yard):
        if not self.committed:
            yard.cmgr.add(self.callback)
        self.committed = True


class MoverStep(StepBase):
    def __init__(self, mover, src, dst, allow_interruption=False, mode="default"):
        super(MoverStep, self).__init__()
        self.mover = mover
        self.src_loc = src
        self.dst_loc = dst
        self.motions = None
        self.mode = mode
        self.allow_interruption = allow_interruption

    def __call__(self, op, est):
        if not self.executed:
            self.cal_pred(op, est)
            self.cal_start_time(op, est)

            op.mark_loc(self.mover, self.start_time, self.src_loc)
            rt, self.motions = self.mover.create_motions(
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

    def commit(self, yard):
        if not self.committed:
            self.mover.commit_motions(self.motions)
        self.committed = True


class AndStep(StepBase):
    def __init__(self, *steps):
        super(AndStep, self).__init__()
        self.steps = list(steps)

    def __call__(self, op, est):
        if not self.executed:
            self.cal_pred(op, est)
            self.cal_start_time(op, est)
            self.finish_time = 0
            self.next_time = 0
            for step in self.steps:
                step(op, est)
                self.finish_time = max(self.finish_time, step.finish_time)
                self.next_time = max(self.next_time, step.next_time)
        self.executed = True

    def __and__(self, other):
        if isinstance(other, AndStep):
            self.steps.extend(other.steps)
        else:
            self.steps.append(other)
        return self

    def __repr__(self):
        return "<{}>[{}]".format(self.__class__.__name__, " & ".join(repr(s) for s in self.steps))


class OrStep(StepBase):
    def __init__(self, *steps):
        super(OrStep, self).__init__()
        self.steps = list(steps)

    def __call__(self, op, est):
        if not self.executed:
            self.cal_pred(op, est)
            self.cal_start_time(op, est)
            self.finish_time = 0
            self.next_time = inf
            for step in self.steps:
                step(op, est)
                self.finish_time = max(self.finish_time, step.finish_time)
                self.next_time = min(self.next_time, step.next_time)
        self.executed = True

    def __or__(self, other):
        if isinstance(other, AndStep):
            self.steps.extend(other.steps)
        else:
            self.steps.append(other)
        return self

    def __repr__(self):
        return "<{}|{}>[{}]".format(self.__class__.__name__, str(id(self))[-4:], " | ".join(repr(s) for s in self.steps))
