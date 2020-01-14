import random

from tcysim.framework.allocator import SpaceAllocator
from tcysim.utils import V3


class RandomSpaceAllocator(SpaceAllocator):
    def alloc_space(self, box, blocks, *args, **kwargs):
        blocks = list(blocks)
        random.shuffle(blocks)
        for block in blocks:
            locs = list(block.available_cells(box))
            if locs:
                return block, random.choice(locs)
        return None, None

    def slot_for_relocation(self, box, start_bay=None, finish_bay=None):
        i, j, _ = box.location
        block = box.block
        start_bay = i if start_bay is None else start_bay
        finish_bay = i + 1 if finish_bay is None else finish_bay
        step = 1 if start_bay < finish_bay else -1
        for i1 in range(start_bay, finish_bay, step):
            if i1 == i or block.bay_is_valid(box, i1):
                for j1 in range(0, block.rows):
                    if (i1, j1) != (i, j):
                        k = block.count(i1, j1)
                        if box.position_is_valid(block, i1, j1, k):
                            return V3(i1, j1, k)