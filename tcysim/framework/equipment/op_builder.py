from ..operation import Operation
from tcysim.utils.dispatcher import Dispatcher


class OpBuilder(Dispatcher):
    OpCls = Operation

    def __init__(self, equipment):
        self.equipment = equipment
        super(OpBuilder, self).__init__()

    @Dispatcher.on("STORE")
    def build_store(self, op: Operation):
        raise NotImplementedError

    @Dispatcher.on("RELOCATE")
    def build_relocate(self, op: Operation):
        raise NotImplementedError

    @Dispatcher.on("RETRIEVE")
    def build_retrieve(self, op: Operation):
        raise NotImplementedError

    @Dispatcher.on("ADJUST")
    def build_adjust(self, op: Operation):
        raise NotImplementedError

    @Dispatcher.on("MOVE")
    def build_move(self, op: Operation):
        raise NotImplementedError

    def build_and_check(self, time, op: Operation):
        op.extend(self.dispatch(op.op_type.name, "_", op))
        op.dry_run(time)
        itf, other, new_loc = self.equipment.check_interference(op)
        if itf:
            op.itf_other = other
            op.itf_loc = new_loc
        return not itf

    @classmethod
    def new_Op(cls, type, *args, **kwargs):
        return cls.OpCls(cls.OpCls.TYPE[type],  *args, **kwargs)

    @classmethod
    def StoreOp(cls, request):
        return cls.new_Op("STORE", request, request.box)

    @classmethod
    def RetrieveOp(cls, request):
        return cls.new_Op("RETRIEVE", request, request.box)

    @classmethod
    def RelocateOp(cls, request, box, new_loc):
        return cls.new_Op("RELOCATE", request, box, new_loc=new_loc)

    @classmethod
    def AdjustOp(cls, request):
        return cls.new_Op("ADJUST", request)

    def MoveOp(self, dst_loc, load=False, interruptable=True):
        return self.new_Op("MOVE", self.equipment,
                         dst_loc=dst_loc,
                         load=load,
                         interruptable=interruptable)

    def move_steps(self, op, src_loc, dst_loc, load=False):
        raise NotImplementedError

    def adjust_steps(self, op, src_loc, dst_loc):
        raise NotImplementedError
