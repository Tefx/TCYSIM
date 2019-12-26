from enum import Enum, auto

from tcysim.utils.dispatcher import Dispatcher
from .operation import Operation


class OpBuilder(Dispatcher):
    class OpType(Enum):
        STORE = auto()
        RETRIEVE = auto()
        RESHUFFLE = auto()
        ADJUST = auto()

    def __init__(self, equipment):
        self.equipment = equipment
        super(OpBuilder, self).__init__()

    def build(self, op: Operation):
        op.extend(self.dispatch(op.op_type, op))

    @Dispatcher.on(OpType.STORE)
    def build_store(self, op: Operation):
        yield from self.move_steps(op, self.equipment.local_coord(), op.access_loc)
        yield op.wait(self.equipment.GRASP_TIME)
        yield op.emit_signal("off_agv")
        yield from self.move_steps(op, op.access_loc, op.container_loc, load=True)
        yield op.emit_signal("on_block")
        yield op.wait(self.equipment.RELEASE_TIME)
        with op.allow_interruption(self.equipment):
            yield from self.idle_steps(op, op.container_loc)

    @Dispatcher.on(OpType.RETRIEVE)
    def build_retrieve(self, op: Operation):
        yield from self.move_steps(op, self.equipment.local_coord(), op.container_loc)
        yield op.emit_signal("off_block")
        yield op.wait(self.equipment.GRASP_TIME)
        yield from self.move_steps(op, op.container_loc, op.access_loc, load=True)
        yield op.wait(self.equipment.RELEASE_TIME)
        yield op.emit_signal("on_agv")
        with op.allow_interruption(self.equipment):
            yield from self.idle_steps(op, op.access_loc)

    @Dispatcher.on(OpType.RESHUFFLE)
    def build_reshuffle(self, op: Operation):
        yield from self.move_steps(op, self.equipment.local_coord(), op.src_loc)
        yield op.emit_signal("reshuffle_pickup")
        yield op.wait(self.equipment.GRASP_TIME)
        yield from self.move_steps(op, op.src_loc, op.dst_loc, load=True)
        yield op.wait(self.equipment.RELEASE_TIME)
        yield op.emit_signal("reshuffle_putdown")
        if op.require_reset:
            with op.allow_interruption(self.equipment):
                yield from self.idle_steps(op, op.dst_loc)

    @Dispatcher.on(OpType.ADJUST)
    def build_adjust(self, op: Operation):
        yield op.emit_signal("adjustment_started")
        # print("REQ BUILDER", self.equipment.local_coord(), op.dst_loc)
        yield from self.adjust_steps(op, self.equipment.local_coord(), op.dst_loc)

    @classmethod
    def StoreOp(cls, request):
        return Operation(cls.OpType.STORE, request)

    @classmethod
    def RetrieveOp(cls, request):
        return Operation(cls.OpType.RETRIEVE, request)

    @classmethod
    def ReshuffleOp(cls, request, reset):
        return Operation(cls.OpType.RESHUFFLE, request, require_reset=reset)

    @classmethod
    def AdjustOp(cls, request):
        return Operation(cls.OpType.ADJUST, request)

    def move_steps(self, op, src_loc, dst_loc, load=False):
        raise NotImplementedError

    def adjust_steps(self, op, src_loc, dst_loc):
        raise NotImplementedError

    def idle_steps(self, op, cur_loc):
        raise NotImplementedError


