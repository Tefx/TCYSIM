import os
import sys

sys.path.extend([
    "../",
    "../../pesim",
    ])
os.environ['PATH'] = "../libtcy/msvc/Release" + os.pathsep + os.environ['PATH']

from tcysim.framework.roles.generator import BoxGenerator
from tcysim.framework.motion.mover import Spec
from tcysim.implementation.entity import Lane, StackingBlock, Crane, Component, TEU
from tcysim.implementation.space_allocator.stacking import SimpleStackingBlockAllocator
from tcysim.framework.yard import Yard
from tcysim.framework.box import Box
from tcysim.utils import V3

import random


class SimpleYard(Yard):
    SpaceAllocator = SimpleStackingBlockAllocator


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


class SimpleBoxGenerator(BoxGenerator):
    def next_time(self, time):
        return time + random.uniform(200, 500)

    def store_time(self, alloc_time):
        return alloc_time + random.uniform(5, 10)

    def retrieve_time(self, store_time):
        return store_time + random.uniform(3600 * 12, 3600 * 24)

    def new_box(self):
        return Box(str(int(self.time)).encode("utf-8"), size=random.choice((20, 40)))


if __name__ == '__main__':
    yard = SimpleYard()

    lanes = [
        Lane(i, V3(0, i * TEU.WIDTH * 2, 0), length=20, width=TEU.WIDTH * 2, rotate=0)
        for i in range(4)
        ]
    block = StackingBlock(yard, V3(25, 0, 0), V3(16, 8, 6), rotate=0, lanes=lanes)
    rmg = RMG(yard, block, 0)
    yard.deploy(block, [rmg])

    # yard.install_observer(PositionTracer, start_or_resume =3600 * 24, end =3600 * 32, interval=1)
    yard.install_generator(SimpleBoxGenerator, first_time=0)

    yard.start()
    yard.run_until(3600 * 32)

    # yard.observer.dump("log")
    # for record in yard.observer:
    #     print(*record)

    print("Finish.")

    # with open(".log", "rb") as f:
    #     tmp = pickle.load(f)
    #
    # for time, ycs, bs in tmp:
    #     print(time, ycs, bs)
    #     if b'4723' in bs:
    #         print(time, ycs, bs[b'4723'])
