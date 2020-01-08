from tcysim.framework.equipment import OpBuilder as OpBuilderBase
from tcysim.framework.operation import OpType, Operation
from tcysim.utils.dispatcher import Dispatcher


class OpBuilder(OpBuilderBase):
    @Dispatcher.on(OpType.STORE)
    def build_store(self, op: Operation):
        request = op.request
        box = request.box
        lane = request.lane
        dst_loc = getattr(request, "dst_loc", None)
        op.access_loc = self.equipment.coord_from_box(box.access_coord(lane, self.equipment))
        op.container_loc = self.equipment.coord_from_box(box.store_coord(self.equipment, loc=dst_loc))
        access_ready_loc = self.equipment.coord_ready_from(op.access_loc)
        container_ready_loc = self.equipment.coord_ready_from(op.container_loc)

        yield op.emit_signal("start_or_resume")
        yield from self.move_steps(op, self.equipment.local_coord(), access_ready_loc)
        yield from self.move_steps(op, access_ready_loc, op.access_loc)
        yield op.wait(self.equipment.GRASP_TIME)
        yield op.emit_signal("off_agv")
        yield from self.move_steps(op, op.access_loc, op.container_loc, load=True)
        yield op.emit_signal("in_block")
        yield op.wait(self.equipment.RELEASE_TIME)
        yield from self.move_steps(op, op.container_loc, container_ready_loc)
        yield op.emit_signal("finish_or_fail")

    @Dispatcher.on(OpType.RETRIEVE)
    def build_retrieve(self, op: Operation):
        request = op.request
        box = request.box
        lane = request.lane
        op.access_loc = self.equipment.coord_from_box(box.access_coord(lane, self.equipment))
        op.container_loc = self.equipment.coord_from_box(box.current_coord(self.equipment))
        access_ready_loc = self.equipment.coord_ready_from(op.access_loc)
        container_ready_loc = self.equipment.coord_ready_from(op.container_loc)

        yield op.emit_signal("start_or_resume")
        yield from self.move_steps(op, self.equipment.local_coord(), container_ready_loc)
        yield from self.move_steps(op, container_ready_loc, op.container_loc)
        yield op.wait(self.equipment.GRASP_TIME)
        yield op.emit_signal("off_block")
        yield from self.move_steps(op, op.container_loc, op.access_loc, load=True)
        yield op.emit_signal("on_agv")
        yield op.wait(self.equipment.RELEASE_TIME)
        yield from self.move_steps(op, op.access_loc, access_ready_loc)
        yield op.emit_signal("finish_or_fail")

    @Dispatcher.on(OpType.RELOCATE)
    def build_relocate(self, op: Operation):
        op.src_loc = self.equipment.coord_from_box(op.box.current_coord(self.equipment))
        op.dst_loc = self.equipment.coord_from_box(op.box.store_coord(self.equipment, op.new_loc))
        src_ready_loc = self.equipment.coord_ready_from(op.src_loc)
        dst_ready_loc = self.equipment.coord_ready_from(op.dst_loc)

        yield op.emit_signal("rlct_start_or_resume")
        yield from self.move_steps(op, self.equipment.local_coord(), src_ready_loc)
        yield from self.move_steps(op, src_ready_loc, op.src_loc)
        yield op.wait(self.equipment.GRASP_TIME)
        yield op.emit_signal("rlct_pick_up")
        yield from self.move_steps(op, op.src_loc, op.dst_loc, load=True)
        yield op.emit_signal("rlct_put_down")
        yield op.wait(self.equipment.RELEASE_TIME)
        yield from self.move_steps(op, op.dst_loc, dst_ready_loc)
        yield op.emit_signal("rlct_finish_or_fail")

    @Dispatcher.on(OpType.ADJUST)
    def build_adjust(self, op: Operation):
        other = op.request.blocking_request.equipment
        op.dst_loc = op.request.new_loc
        yield op.emit_signal("start_or_resume")
        if self.equipment.adjust_is_necessary(other, op.dst_loc):
            yield from self.adjust_steps(op, self.equipment.local_coord(), op.dst_loc)
        yield op.emit_signal("finish_or_fail")

    @Dispatcher.on(OpType.MOVE)
    def build_move(self, op: Operation):
        load = op.load
        dst_loc = op.dst_loc
        if op.interruptable:
            with op.allow_interruption(self.equipment, query_task_before_perform=False):
                yield from self.move_steps(op, self.equipment.local_coord(), dst_loc, load)
        else:
            yield from self.move_steps(op, self.equipment.local_coord(), dst_loc, load)

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
