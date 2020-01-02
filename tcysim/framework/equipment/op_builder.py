from tcysim.utils.dispatcher import Dispatcher
from ..operation import Operation, OpType as _OpType


class OpBuilder(Dispatcher):
    OpType = _OpType

    def __init__(self, equipment):
        self.equipment = equipment
        super(OpBuilder, self).__init__()

    def build(self, op: Operation):
        op.extend(self.dispatch(op.op_type, "_", op))

    @Dispatcher.on(OpType.STORE)
    def build_store(self, op: Operation):
        request = op.request
        box = request.box
        lane = request.lane
        op.access_loc = self.equipment.coord_from_box(box.access_coord(lane, self.equipment))
        op.container_loc = self.equipment.coord_from_box(box.store_coord(self.equipment))

        yield op.emit_signal("start_or_resume")
        yield from self.move_steps(op, self.equipment.local_coord(), op.access_loc)
        yield op.wait(self.equipment.GRASP_TIME)
        yield op.emit_signal("off_agv")
        yield from self.move_steps(op, op.access_loc, op.container_loc, load=True)
        yield op.emit_signal("in_block")
        yield op.wait(self.equipment.RELEASE_TIME)
        yield op.emit_signal("finish_or_fail")
        with op.allow_interruption(self.equipment):
            yield from self.idle_steps(op, op.container_loc)

    @Dispatcher.on(OpType.RETRIEVE)
    def build_retrieve(self, op: Operation):
        request = op.request
        box = request.box
        lane = request.lane
        op.access_loc = self.equipment.coord_from_box(box.access_coord(lane, self.equipment))
        op.container_loc = self.equipment.coord_from_box(box.current_coord(self.equipment))

        yield op.emit_signal("start_or_resume")
        yield from self.move_steps(op, self.equipment.local_coord(), op.container_loc)
        yield op.emit_signal("off_block")
        yield op.wait(self.equipment.GRASP_TIME)
        yield from self.move_steps(op, op.container_loc, op.access_loc, load=True)
        yield op.wait(self.equipment.RELEASE_TIME)
        yield op.emit_signal("on_agv")
        yield op.emit_signal("finish_or_fail")
        with op.allow_interruption(self.equipment):
            yield from self.idle_steps(op, op.access_loc)

    @Dispatcher.on(OpType.RELOCATE)
    def build_relocate(self, op: Operation):
        box = op.box
        dst_loc = op.new_loc
        op.src_loc = self.equipment.coord_from_box(box.current_coord(self.equipment))
        op.dst_loc = self.equipment.coord_from_box(box.store_coord(self.equipment, dst_loc))

        yield op.emit_signal("rlct_start_or_resume")
        yield from self.move_steps(op, self.equipment.local_coord(), op.src_loc)
        yield op.emit_signal("rlct_pick_up")
        yield op.wait(self.equipment.GRASP_TIME)
        yield from self.move_steps(op, op.src_loc, op.dst_loc, load=True)
        yield op.wait(self.equipment.RELEASE_TIME)
        yield op.emit_signal("rlct_put_down")
        yield op.emit_signal("rlct_finish_or_fail")
        if op.require_reset:
            with op.allow_interruption(self.equipment):
                yield from self.idle_steps(op, op.dst_loc)

    @Dispatcher.on(OpType.MOVE)
    def build_adjust(self, op: Operation):
        other = op.request.blocking_request.equipment
        op.dst_loc = op.request.new_loc
        yield op.emit_signal("start_or_resume")
        if self.equipment.adjust_is_necessary(other, op.dst_loc):
            yield from self.adjust_steps(op, self.equipment.local_coord(), op.dst_loc)
        yield op.emit_signal("finish_or_fail")

    def build_and_check(self, time, op:Operation):
        self.build(op)
        op.dry_run(time)
        itf, other, new_loc = self.equipment.check_interference(op)
        if itf:
            op.itf_other = other
            op.itf_loc = new_loc
            return False
        return True

    @classmethod
    def StoreOp(cls, request):
        return Operation(cls.OpType.STORE, request)

    @classmethod
    def RetrieveOp(cls, request):
        return Operation(cls.OpType.RETRIEVE, request)

    @classmethod
    def RelocateOp(cls, request, box, new_loc, reset):
        return Operation(cls.OpType.RELOCATE, request, box=box, new_loc=new_loc, require_reset=reset)

    @classmethod
    def AdjustOp(cls, request):
        return Operation(cls.OpType.MOVE, request)

    def move_steps(self, op, src_loc, dst_loc, load=False):
        raise NotImplementedError

    def adjust_steps(self, op, src_loc, dst_loc):
        raise NotImplementedError

    def idle_steps(self, op, cur_loc):
        raise NotImplementedError


