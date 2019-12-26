import os
import sys
from enum import auto

from tcysim.framework.request import ReqStatus

sys.path.extend([
    "../",
    "../../pesim",
    ])
os.environ['PATH'] = "../libtcy/msvc/Release" + os.pathsep + os.environ['PATH']

from tcysim.framework.management import TaskScheduler
from tcysim.framework.generator import BoxGenerator
from tcysim.framework.motion.mover import Spec
from tcysim.implementation.entity import Lane, StackingBlock, Crane, Component, TEU
from tcysim.implementation.management.space import SimpleStackingBlockAllocator
from tcysim.implementation.observer.position_tracer import PositionTracer
from tcysim.framework.yard import Yard
from tcysim.framework.box import Box
from tcysim.utils import V3

import random


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


class MultiCraneTaskScheduler(TaskScheduler):
    def choose_equipment(self, time, request, equipments):
        bay = request.box.location[0]
        if bay < 8:
            idx = 0
        else:
            idx = 1
        for equipment in equipments:
            if equipment.idx == idx:
                return equipment

    def choose_task(self, time, equipment, tasks):
        tmp = None
        tasks = list(tasks)
        print("\n>>>[{}]SCHEDULE".format(self.yard.env.current_time), equipment.idx, [task.req_type for task in tasks], "\n")
        tasks.sort(key=lambda x:x.arrival_time)
        for task in tasks:
            if task.req_type == task.block.ReqHandler.ReqType.ADJUST:
                return task
            elif task.status == ReqStatus.SENTBACK:
                return task
            else:
                if not tmp:
                    tmp = task
        return tmp


class SimpleYard(Yard):
    SpaceAllocator = SimpleStackingBlockAllocator
    TaskScheduler = MultiCraneTaskScheduler


if __name__ == '__main__':
    yard = SimpleYard()

    lanes = [
        Lane(i, V3(0, i * TEU.WIDTH * 2, 0), length=20, width=TEU.WIDTH * 2, rotate=0)
        for i in range(4)
        ]
    lanes.append(Lane(5, V3(25, -TEU.WIDTH * 2, 0), length=TEU.LENGTH * 50, width=TEU.WIDTH * 2, rotate=0))
    lanes.append(Lane(6, V3(25, TEU.WIDTH * 8, 0), length=TEU.LENGTH * 50, width=TEU.WIDTH * 2, rotate=0))
    block = StackingBlock(yard, V3(25, 0, 0), V3(16, 8, 6), rotate=0, lanes=lanes)
    rmg1 = RMG(yard, block, 0, idx=0)
    rmg2 = RMG(yard, block, -1, idx=1)
    yard.deploy(block, [rmg1])

    yard.install_observer(PositionTracer, start =3600 * 24, end =3600 * 28, interval=1)
    yard.install_generator(SimpleBoxGenerator, first_time=0)

    yard.start()
    yard.run_until(3600 * 32)

    yard.observer.dump("log")
    for record in yard.observer:
        print(*record)

    for req in yard.tmgr.requests:
        if req.status < ReqStatus.FINISHED:
            print(req, req.arrival_time, req.block.is_locked(req.box.location), req.box.location,
                  req.block.req_handler.validate(3600*32, req))

    print("Finish.")
