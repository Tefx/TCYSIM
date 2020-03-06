from ..operation import Operation, OpType as _OpType
from tcysim.utils.dispatcher import Dispatcher


class OpBuilder(Dispatcher):
    OpType = _OpType

    def __init__(self, equipment):
        self.equipment = equipment
        super(OpBuilder, self).__init__()

    def build(self, op: Operation):
        op.extend(self.dispatch(op.op_type, "_", op))

    @Dispatcher.on(OpType.STORE)
    def build_store(self, op: Operation):
        raise NotImplementedError

    @Dispatcher.on(OpType.RELOCATE)
    def build_relocate(self, op: Operation):
        raise NotImplementedError

    @Dispatcher.on(OpType.RETRIEVE)
    def build_retrieve(self, op: Operation):
        raise NotImplementedError

    @Dispatcher.on(OpType.ADJUST)
    def build_adjust(self, op: Operation):
        raise NotImplementedError

    @Dispatcher.on(OpType.MOVE)
    def build_move(self, op: Operation):
        raise NotImplementedError

    def build_and_check(self, time, op: Operation):
        self.build(op)
        op.dry_run(time)
        itf, other, new_loc = self.equipment.check_interference(op)
        if itf:
            op.itf_other = other
            op.itf_loc = new_loc
        return not itf

    @classmethod
    def StoreOp(cls, request):
        return Operation(cls.OpType.STORE, request, request.box)

    @classmethod
    def RetrieveOp(cls, request):
        return Operation(cls.OpType.RETRIEVE, request, request.box)

    @classmethod
    def RelocateOp(cls, request, box, new_loc):
        return Operation(cls.OpType.RELOCATE, request, box, new_loc=new_loc)

    @classmethod
    def AdjustOp(cls, request):
        return Operation(cls.OpType.ADJUST, request)

    def MoveOp(self, dst_loc, load=False, interruptable=True):
        return Operation(self.OpType.MOVE, self.equipment,
                         dst_loc=dst_loc,
                         load=load,
                         interruptable=interruptable)

    def move_steps(self, op, src_loc, dst_loc, load=False):
        raise NotImplementedError

    def adjust_steps(self, op, src_loc, dst_loc):
        raise NotImplementedError
