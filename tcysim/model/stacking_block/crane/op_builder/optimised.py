from .base import OpBuilderForCrane
from tcysim.utils import TEU


class OptimisedOpBuilderForCrane(OpBuilderForCrane):
    def move_steps(self, op, src_loc, dst_loc, load=False):
        hoist_mode = "rated load" if load else "no load"
        equipment = self.equipment

        if op.request:
            block = op.request.block
        elif equipment.num_blocks == 1:
            block = equipment.blocks[0]
        else:
            yield from super(OptimisedOpBuilderForCrane, self).move_steps(op, src_loc, dst_loc)
            return

        hoist_move = op.move(equipment.hoist, src_loc, dst_loc, hoist_mode)

        if src_loc.set1("z", 0) == dst_loc.set1("z", 0):
            yield hoist_move
            return

        src_local_in_block = equipment.transform_to(src_loc, block)
        dst_local_in_block = equipment.transform_to(dst_loc, block)

        src_v, src_h = block.zone_from_coord(src_local_in_block)
        dst_v, dst_h = block.zone_from_coord(dst_local_in_block)

        gantry_move = op.move(equipment.gantry, src_loc, dst_loc)
        trolley_move = op.move(equipment.trolley, src_loc, dst_loc)

        if src_v != 1 and dst_v == src_v and (src_h == 1 or dst_h == src_h):
            yield gantry_move, trolley_move, hoist_move
            return

        if src_h != 1 and dst_h == src_h and (src_v == 1 or dst_v == src_v):
            yield gantry_move, trolley_move, hoist_move
            return

        max_height = block.max_height_within(src_local_in_block, dst_local_in_block) + equipment.clearance_above_box
        if max_height < dst_loc.z:
            max_height = dst_loc.z
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
        equipment = op.equipment
        block = op.request.block
        max_height = block.max_height_within(
            equipment.transform_to(src_loc, block),
            equipment.transform_to(dst_loc, block)) + op.equipment.clearance_above_box
        dst_loc.z = max(src_loc.z, max_height)
        yield from self.move_steps(op, src_loc, dst_loc, load=False)

    def adjust_is_necessary(self, other_equipment, dst_loc):
        # if self.equipment.blocks[0].id == 49:
        #     print(self.equipment.idx, other_equipment.current_coord(self.equipment).x, dst_loc.x, self.equipment.current_coord().x)
        return (other_equipment.current_coord(transform_to=self.equipment).x - dst_loc.x) * \
               (self.equipment.current_coord().x - dst_loc.x) > 0
