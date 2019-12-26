from tcysim.framework.motion.motion import Motion


class StepABC:
    def __rshift__(self, other):
        if isinstance(other, NullStep):
            return self
        else:
            return SStep(self, other)

    def __or__(self, other):
        if isinstance(other, NullStep):
            return self
        else:
            return PStep(self, other)

    def __call__(self, op, start_time):
        raise NotImplementedError

    def commit(self, yard):
        raise NotImplementedError


class NullStep(StepABC):
    def __rshift__(self, other):
        return other

    def __or__(self, other):
        return other


class MoverStep(StepABC):
    def __init__(self, mover, src, dst, allow_interruption=False, mode="default"):
        super().__init__()
        self.mover = mover
        self.src_loc = src
        self.dst_loc = dst
        self.motions = None
        self.mode = mode
        self.allow_interruption = allow_interruption

    def __call__(self, op, start_time):
        op.mark_loc(self.mover, start_time, self.src_loc)
        # if op.op_type == op.request.equipment.OpBuilder.OpType.ADJUST:
        #     print(start_time, self.src_loc, self.mover.axis)
        #     print(self.src_loc, self.dst_loc)
        rt, self.motions = self.mover.create_motions(
            start_time, self.dst_loc - self.src_loc, self.allow_interruption, self.mode)
        op.mark_loc(self.mover, start_time + rt, self.dst_loc)
        # if op.op_type == op.request.equipment.OpBuilder.OpType.ADJUST:
        #     print(start_time + rt, self.dst_loc)
        return start_time + rt

    def commit(self, yard):
        self.mover.commit_motions(self.motions)


class EmptyStep(StepABC):
    def __init__(self, mover, time):
        super().__init__()
        self.time = time
        self.mover = mover
        self.motion = None

    def __call__(self, op, start_time):
        self.motion = Motion(start_time, self.time, 0, 0, allow_interruption=False)
        return start_time + self.time

    def commit(self, yard):
        self.mover.commit_motions((self.motion,))


class CallBackStep(StepABC):
    def __init__(self, callback):
        super().__init__()
        self.callback = callback

    def __call__(self, op, start_time):
        # print("Callback assign time", start_time, self.callback.func)
        self.callback.time = start_time
        return start_time

    def commit(self, yard):
        yard.cmgr.add(self.callback)


class PStep(StepABC):
    def __init__(self, *steps):
        super().__init__()
        self.steps = steps

    def __call__(self, op, start_time):
        ft_max = start_time
        for step in self.steps:
            ft_max = max(ft_max, step(op, start_time))
        return ft_max

    def commit(self, yard):
        for step in self.steps:
            step.commit(yard)


class SStep(StepABC):
    def __init__(self, *steps):
        super().__init__()
        self.steps = steps

    def __call__(self, op, start_time):
        # print(op.op_type.name, op.step)
        st = start_time
        for step in self.steps:
            st = step(op, st)
        return st

    def commit(self, yard):
        for step in self.steps:
            step.commit(yard)
