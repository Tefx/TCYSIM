from tcysim.framework import OpBuilderBase, EventReason
from tcysim.utils.dispatcher import Dispatcher

from ..operation import OperationForCrane as Operation


class OpBuilderForCrane(OpBuilderBase):
    OpCls = Operation

    @Dispatcher.on("STORE")
    def build_store(self, op: Operation):
        request = op.request
        box = op.box
        lane = request.lane
        dst_loc = getattr(request, "dst_loc", None)
        op.access_loc = self.equipment.coord_from_box(box.access_coord(lane, transform_to=self.equipment))
        op.container_loc = self.equipment.coord_from_box(box.store_coord(dst_loc, transform_to=self.equipment))
        access_ready_loc = self.equipment.prepare_coord(op.access_loc)
        container_ready_loc = self.equipment.prepare_coord(op.container_loc)

        yield op.emit_signal("start_or_resume")
        yield from self.move_steps(op, self.equipment.current_coord(), access_ready_loc)
        yield from self.move_steps(op, access_ready_loc, op.access_loc)
        yield op.wait(self.equipment.GRASP_TIME)
        yield op.emit_signal("off_agv")
        yield op.sync()
        yield from self.move_steps(op, op.access_loc, access_ready_loc, load=True)
        yield from self.move_steps(op, access_ready_loc, op.container_loc, load=True)
        yield op.emit_signal("in_block")
        yield op.fire_probe("box.after_in_block", box, op, probe_reason=EventReason.CALLBACK.after)
        yield op.wait(self.equipment.RELEASE_TIME)
        yield from self.move_steps(op, op.container_loc, container_ready_loc)
        yield op.emit_signal("finish_or_fail")

    @Dispatcher.on("RETRIEVE")
    def build_retrieve(self, op: Operation):
        request = op.request
        box = op.box
        lane = request.lane
        op.access_loc = self.equipment.coord_from_box(box.access_coord(lane, transform_to=self.equipment))
        op.container_loc = self.equipment.coord_from_box(box.store_coord(transform_to=self.equipment))
        access_ready_loc = self.equipment.prepare_coord(op.access_loc)
        container_ready_loc = self.equipment.prepare_coord(op.container_loc)

        yield op.emit_signal("start_or_resume")
        yield from self.move_steps(op, self.equipment.current_coord(), container_ready_loc)
        yield from self.move_steps(op, container_ready_loc, op.container_loc)
        yield op.fire_probe("box.before_off_block", box, op, probe_reason=EventReason.CALLBACK.before)
        yield op.emit_signal("off_block")
        yield op.wait(self.equipment.GRASP_TIME)
        yield from self.move_steps(op, op.container_loc, access_ready_loc, load=True)
        yield from self.move_steps(op, access_ready_loc, op.access_loc, load=True)
        yield op.wait(self.equipment.RELEASE_TIME)
        yield op.emit_signal("on_agv")
        yield op.sync()
        yield from self.move_steps(op, op.access_loc, access_ready_loc)
        yield op.emit_signal("finish_or_fail")

    @Dispatcher.on("RELOCATE")
    def build_relocate(self, op: Operation):
        box = op.box
        op.src_loc = self.equipment.coord_from_box(box.store_coord(transform_to=self.equipment))
        op.dst_loc = self.equipment.coord_from_box(box.store_coord(op.new_loc, transform_to=self.equipment))
        src_ready_loc = self.equipment.prepare_coord(op.src_loc)
        dst_ready_loc = self.equipment.prepare_coord(op.dst_loc)

        yield op.emit_signal("rlct_start_or_resume")
        yield from self.move_steps(op, self.equipment.current_coord(), src_ready_loc)
        yield from self.move_steps(op, src_ready_loc, op.src_loc)
        yield op.wait(self.equipment.GRASP_TIME)
        yield op.fire_probe("box.before_off_block", box, op, probe_reason=EventReason.CALLBACK.before)
        yield op.emit_signal("rlct_pick_up")
        yield from self.move_steps(op, op.src_loc, op.dst_loc, load=True)
        yield op.emit_signal("rlct_put_down")
        yield op.fire_probe("box.after_in_block", box, op, probe_reason=EventReason.CALLBACK.after)
        yield op.wait(self.equipment.RELEASE_TIME)
        yield from self.move_steps(op, op.dst_loc, dst_ready_loc)
        yield op.emit_signal("rlct_finish_or_fail")

    @Dispatcher.on("ADJUST")
    def build_adjust(self, op: Operation):
        other = op.request.blocking_request.equipment
        op.dst_loc = op.request.new_loc
        yield op.emit_signal("start_or_resume")
        if self.adjust_is_necessary(other, op.dst_loc):
            yield from self.adjust_steps(op, self.equipment.current_coord(), op.dst_loc)
        yield op.emit_signal("finish_or_fail")

    def adjust_is_necessary(self, other_equipment, dst_loc):
        return (other_equipment.current_coord(transform_to=self.equipment) - dst_loc).dot_product(
            self.equipment.current_coord() - dst_loc) >= 0

    @Dispatcher.on("MOVE")
    def build_move(self, op: Operation):
        load = op.load
        dst_loc = op.dst_loc
        if op.interruptable:
            with op.allow_interruption(self.equipment, query_task_before_perform=False):
                yield from self.move_steps(op, self.equipment.current_coord(), dst_loc, load)
        else:
            yield from self.move_steps(op, self.equipment.current_coord(), dst_loc, load)

    def move_steps(self, op, src_loc, dst_loc, load=False):
        hoist_mode = "rated load" if load else "no load"

        hm2h = op.move(self.equipment.hoist, src_loc, self.equipment.hoist.max_height, hoist_mode)
        gm = op.move(self.equipment.gantry, src_loc, dst_loc)
        tm = op.move(self.equipment.trolley, src_loc, dst_loc)
        tm2d = op.move(self.equipment.hoist, self.equipment.hoist.max_height, dst_loc, hoist_mode)

        tm2d <<= gm & tm

        yield hm2h
        yield gm, tm, tm2d

    def adjust_steps(self, op, src_loc, dst_loc):
        dst_loc.z = self.equipment.hoist.max_height
        yield from self.move_steps(op, src_loc, dst_loc, load=False)

    def idle_steps(self, op, cur_loc):
        dst_loc = cur_loc.set1("z", self.equipment.hoist.max_height)
        yield from self.move_steps(op, cur_loc, dst_loc, load=False)

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