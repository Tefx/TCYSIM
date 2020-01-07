from tcysim.framework.equipment import OpBuilder as OpBuilderBase
from tcysim.utils import TEU


class OpBuilder(OpBuilderBase):
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


class OptimizedOpBuilder(OpBuilder):
    def move_steps(self, op, src_loc, dst_loc, load=False):
        hoist_mode = "rated load" if load else "no load"
        equipment = self.equipment

        if op.request:
            block = op.request.block
        elif len(equipment.blocks) == 1:
            block = equipment.blocks[0]
        else:
            yield from super(OptimizedOpBuilder, self).move_steps(op, src_loc, dst_loc)
            return

        hoist_move = op.move(equipment.hoist, src_loc, dst_loc, hoist_mode)

        if src_loc.set1("z", 0) == dst_loc.set1("z", 0):
            yield hoist_move
            return

        src_glbl = equipment.coord_l2g(src_loc)
        dst_glbl = equipment.coord_l2g(dst_loc)

        src_v, src_h = block.coord_zone(src_glbl)
        dst_v, dst_h = block.coord_zone(dst_glbl)

        gantry_move = op.move(equipment.gantry, src_loc, dst_loc)
        trolley_move = op.move(equipment.trolley, src_loc, dst_loc)

        if src_v != 1 and dst_v == src_v and (src_h == 1 or dst_h == src_h):
            yield gantry_move, trolley_move, hoist_move
            return

        if src_h != 1 and dst_h == src_h and (src_v == 1 or dst_v == src_v):
            yield gantry_move, trolley_move, hoist_move
            return

        max_height = block.max_height_within(src_glbl, dst_glbl) + equipment.height_clearance
        max_height = max(dst_loc.z, max_height)
        if load:
            max_height += TEU.HEIGHT

        hoist_move2mh = op.move(equipment.hoist, src_loc, max_height, hoist_mode)
        hoist_move2dst = op.move(equipment.hoist, max_height, dst_loc, hoist_mode)
        hoist_move2dst <<= hoist_move2mh

        if src_loc.z <= max_height:
            if src_v == 1:
                gantry_move <<= hoist_move2mh
            if src_h == 1:
                trolley_move <<= hoist_move2mh
            if src_v != 1 and src_h != 1:
                trolley_move <<= hoist_move2mh

        if dst_v == 1:
            if dst_h == 1:
                hoist_move2dst <<= gantry_move & trolley_move
            else:
                hoist_move2dst <<= gantry_move
        else:
            if dst_h == 1:
                hoist_move2dst <<= trolley_move
            else:
                hoist_move2dst <<= gantry_move | trolley_move

        yield gantry_move, trolley_move, hoist_move2mh, hoist_move2dst

    def adjust_steps(self, op, src_loc, dst_loc):
        dst_loc.y = src_loc.y
        max_height = op.request.block.max_height_within(src_loc, dst_loc) + op.equipment.height_clearance
        dst_loc.z = max(src_loc.z, max_height)
        yield from self.move_steps(op, src_loc, dst_loc, load=False)
