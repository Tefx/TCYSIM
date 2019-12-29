from copy import copy

from tcysim.utils import V3
from tcysim.framework.management import SpaceAllocator
import random


class SimpleStackingBlockAllocator(SpaceAllocator):
    def _dis2box(self, box, v):
        return (abs(box.location[0] - v[0]), abs(box.location[1] - v[1]))

    def available_stack(self, box, block):
        shape = block.shape
        for i in range(shape.x):
            if block.count(i, -1, -1) < shape.z * shape.y - shape.z:
                for j in range(shape.y):
                    k = block.count(i, j)
                    if k < shape.z and box.position_is_valid(block, i, j, k):
                        yield V3(i, j, k)

    def alloc_space(self, box, blocks):
        for block in blocks:
            locs = list(self.available_stack(box, block))
            if locs:
                return block, random.choice(locs)
            # for loc in self.available_stack(box, block):
            #     return block, loc
        return None, None

    def slot_for_reshuffle(self, box):
        i, j, _ = box.location
        block = box.block
        shape = block.shape
        for j1 in range(0, shape.y):
            if j1 != j:
                k = block.count(i, j1)
                if k < shape.z:
                    return V3(i, j1, k)
