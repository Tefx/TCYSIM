from pickle import dump

from tcysim.framework.motion.mover import Spec
from tcysim.framework.observer import Observer
from tcysim.implementation.entity import Lane, StackingBlock, Crane, Component
from tcysim.implementation.space_allocator.stacking import SimpleStackingBlockAllocator
from tcysim.framework.yard import Yard
from tcysim.framework.box import Box
from tcysim.utils import V3

import random


class SimpleYard(Yard):
    SpaceAllocator = SimpleStackingBlockAllocator


class Tracer(Observer):
    def __init__(self, *args, **kwargs):
        super(Tracer, self).__init__(*args, **kwargs)
        self.log = []

    def on_observe(self):
        equ_coords = [coord.to_tuple() for _, coord in self.yard.equipment_coords()]
        box_coords = [(box.id, box.teu, coord.to_tuple()) for box, coord in self.yard.box_coords()]
        self.log.append((self.time, equ_coords, box_coords))

    def __iter__(self):
        for item in self.log:
            yield item

    def dump(self, path):
        with open(path, "wb") as f:
            dump(self.log, f)


class RMG(Crane):
    gantry = Component(
        axis="x",
        specs=Spec(200 / 60, 0.25),
        may_interfere=True)

    trolley = Component(
        axis="y",
        specs=Spec(150 / 60, 0.625)
        )

    hoist = Component(
        axis="z",
        specs={
            "no load":    Spec(v=130 / 60, a=0.6),
            "rated load": Spec(v=1, a=0.6)
            },
        max_height=30)


if __name__ == '__main__':
    yard = SimpleYard()

    lane = Lane(0, V3(0, 0, 0), length=20, width=5, rotate=90)
    block = StackingBlock(yard, V3(0, 25, 0), V3(10, 6, 5), rotate=90, lanes=[lane])
    rmg = RMG(yard, block, 0)
    yard.deploy(block, [rmg])

    print(lane.offset, lane.size)
    print(block.offset, block.size)

    yard.install_observer(Tracer, interval=1)

    yard.start()

    # box = Box(b"1", size=20)
    boxes = []
    for i in range(10 * 6 * 2):
        box = Box(str(i).encode("utf-8"), size=random.choice([20, 40]))
        boxes.append(box)
        succeed = yard.alloc(0, box)
        assert succeed
        print(i, box.location)

    for box in boxes:
        yard.store(0, box, lane)

    # box = boxes[0]
    # for box in boxes:
    #     if box.state >= box.STATE_STORING:
    #         yard.retrieve(500, box, lane)

    yard.run_until(7200)

    yard.observer.dump(".log")
    # for record in yard.observer:
    #     print(*record)

    # for i in range(0, 300, 1):
    #     if i == 115:
    #         yard.retrieve(115, box, lane)
    #     yard.run_until(i)
    #     yc_coord = rmg.coord()
    #     box_coord = box.coord()
    #     print("[i]:")
    #     print("\t{}".format([coord.to_tuple() for _, coord in yard.equipment_coords()]))
    #     print("\t{}".format([coord.to_tuple() for _, coord in yard.box_coords()]))
#
