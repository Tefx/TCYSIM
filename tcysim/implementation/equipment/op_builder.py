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

        src_glbl = equipment.coord_l2g(src_loc)
        dst_glbl = equipment.coord_l2g(dst_loc)

        if src_loc.set1("z", 0) != dst_loc.set1("z", 0):
            max_height = block.max_height_within(src_glbl, dst_glbl) + equipment.height_clearance
        else:
            max_height = 0
        if load:
            max_height += TEU.HEIGHT
        max_height = max(dst_loc.z, max_height)

        src_v, src_h = block.coord_zone(src_glbl)
        dst_v, dst_h = block.coord_zone(dst_glbl)
        src_at_high = src_loc.z > max_height

        gantry_move = op.move(equipment.gantry, src_loc, dst_loc)
        trolley_move = op.move(equipment.trolley, src_loc, dst_loc)
        hoist_move2mh = op.move(equipment.hoist, src_loc, max_height, hoist_mode)
        hoist_move2dst = op.move(equipment.hoist, max_height, dst_loc, hoist_mode)
        hoist_move = op.move(equipment.hoist, src_loc, dst_loc, hoist_mode)

        # (0, ?) => ?
        if src_v in (0, 2):
            # (0, 0)  => ?
            if src_h in (0, 2):
                # (0, 0) => (0, *)/(*, 0)
                if dst_v == src_v or dst_v == src_h:
                    yield gantry_move | trolley_move | hoist_move
                # (0, 0) => (2, 1), (2, 2)
                elif dst_v in (0, 2):
                    if src_at_high:
                        yield gantry_move | ((trolley_move | hoist_move2mh) >> hoist_move2dst)
                    else:
                        yield gantry_move | (hoist_move2mh >> trolley_move >> hoist_move2dst)
                # (0, 0) => (1, ?)
                else:
                    # (0, 0) => (1, 2)
                    if dst_h in (0, 2):
                        if src_at_high:
                            yield trolley_move | ((gantry_move | hoist_move2mh) >> hoist_move2dst)
                        else:
                            yield (hoist_move2mh >> trolley_move) | gantry_move
                            yield hoist_move2dst
                    # (0, 0) => (1, 1)
                    else:
                        if src_at_high:
                            yield gantry_move | trolley_move | hoist_move2mh
                            yield hoist_move2dst
                        else:
                            yield gantry_move | (hoist_move2mh >> trolley_move)
                            yield hoist_move2dst
            # (0, 1)  => ?
            else:
                # (0, 1) => (0, *)
                if dst_v == src_v:
                    yield gantry_move | trolley_move | hoist_move
                # (0, 1) => (2, 1), (2, 2)
                elif dst_v in (0, 2):
                    if src_at_high:
                        yield gantry_move | (trolley_move | hoist_move2mh) >> hoist_move2dst
                    else:
                        yield gantry_move | hoist_move2mh >> trolley_move >> hoist_move2dst
                # (0, 1) => (1, ?)
                else:
                    # (0, 1) => (1, 0), (1, 2)
                    if dst_h in (0, 2):
                        if src_at_high:
                            yield trolley_move | (gantry_move | hoist_move2mh) >> hoist_move2dst
                        else:
                            yield gantry_move | hoist_move2mh >> trolley_move
                            yield hoist_move2dst
                    # (0, 1) => (1, 1)
                    else:
                        if src_at_high:
                            yield gantry_move | trolley_move | hoist_move2mh
                            yield hoist_move2dst
                        else:
                            yield gantry_move | (hoist_move2mh >> trolley_move)
                            yield hoist_move2dst
        # (1, ?) => ?
        else:
            # (1, 0) => ?
            if src_h in (0, 2):
                # (1, 0) => (1, *)
                if dst_h == src_h:
                    yield gantry_move | trolley_move | hoist_move
                # (1, 0) => (0, ?), (2, ?)
                elif dst_v in (0, 2):
                    # (1, 0) => (0, 2), (2, 2)
                    if dst_h in (0, 2):
                        if src_at_high:
                            yield trolley_move | (gantry_move | hoist_move2mh) >> hoist_move2dst
                        else:
                            yield trolley_move | (hoist_move2mh >> gantry_move >> hoist_move2dst)
                    # (1, 0) => (0, 1), (2, 1)
                    else:
                        if src_at_high:
                            yield gantry_move | (trolley_move | hoist_move2mh) >> hoist_move2dst
                        else:
                            yield trolley_move | (hoist_move2mh >> gantry_move)
                            yield hoist_move2dst
                # (1, 0) => (1, ?)
                else:
                    # (1, 0) => (1, 2)
                    if dst_h in (0, 2):
                        if src_at_high:
                            yield trolley_move | ((gantry_move | hoist_move2mh) >> hoist_move2dst)
                        else:
                            yield trolley_move | (hoist_move2mh >> gantry_move >> hoist_move2dst)
                    # (1, 0) => (1, 1)
                    else:
                        if src_at_high:
                            yield gantry_move | trolley_move | hoist_move2mh
                            yield hoist_move2dst
                        else:
                            yield trolley_move | (hoist_move2mh >> gantry_move)
                            yield hoist_move2dst
            # (1, 1) => ?
            else:
                # (1, 1) => (0, *), (2, *)
                if dst_v in (0, 2):
                    if src_at_high:
                        yield gantry_move | (trolley_move | hoist_move2mh) >> hoist_move2dst
                    else:
                        yield hoist_move2mh
                        yield gantry_move | (trolley_move >> hoist_move2dst)
                # (1, 1) => (1, ?)
                else:
                    # (1, 1) => (1, 0), (1, 2)
                    if dst_h in (0, 2):
                        if src_at_high:
                            yield trolley_move | ((gantry_move | hoist_move2mh) >> hoist_move2dst)
                        else:
                            yield hoist_move2mh
                            yield trolley_move | (gantry_move >> hoist_move2dst)
                    # (1, 1) => (1, 1)
                    else:
                        if src_at_high:
                            yield gantry_move | trolley_move | hoist_move2mh
                            yield hoist_move2dst
                        else:
                            yield hoist_move2mh
                            yield gantry_move | trolley_move
                            yield hoist_move2dst

    def adjust_steps(self, op, src_loc, dst_loc):
        dst_loc.y = src_loc.y
        dst_loc.z = max(src_loc.z, op.request.block.max_height_within(src_loc, dst_loc))
        yield from self.move_steps(op, src_loc, dst_loc, load=False)
