import os
import sys


sys.path.extend([
    "../",
    "../../pesim",
    ])
os.environ['PATH'] = "../libtcy/msvc/Release" + os.pathsep + os.environ['PATH']
os.environ['PATH'] = "../libtcy/cmake-build-debug" + os.pathsep + os.environ['PATH']

from tcysim.framework.request import ReqStatus, Request
from tcysim.framework.management import TaskScheduler
from tcysim.framework.generator import BoxGenerator
from tcysim.framework.motion.mover import Spec
from tcysim.implementation.entity import Lane, StackingBlock, Crane, Component, TEU
from tcysim.implementation.management.space import SimpleStackingBlockAllocator
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
        return time + random.uniform(200, 600)

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

    def rank_task(self, task:Request):
        if task.req_type == task.equipment.req_handler.ReqType.ADJUST:
            return 0, task.ready_time
        elif task.status == ReqStatus.RESUME_READY:
            return 1, -task.ready_time
        else:
            return 2, task.ready_time

    def choose_task(self, time, equipment, tasks):
        return min(filter(Request.is_ready, tasks), key=self.rank_task, default=None)


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
    yard.deploy(block, [rmg1, rmg2])

    # yard.install_observer(PositionTracer, start =3600 * 20, end =3600 * 24, interval=1)
    yard.install_generator(SimpleBoxGenerator, first_time=0)

    yard.start()
    yard.run_until(3600 * 24)

    if yard.observer:
        yard.observer.dump("log")
    # for record in yard.observer:
    #     print(*record)

    print("{:<12}: {}".format("TOTAL", len(yard.tmgr.requests)))
    print("{:<12}: {}".format("TOTAL (AC)", len([req for req in yard.tmgr.requests if req.finish_time > req.start_time])))
    print("{:<12}: {}".format("TOTAL (NA)", len([req for req in yard.tmgr.requests if req.req_type != req.TYPE.ADJUST])))
    print("{:<12}: {}".format("TOTAL (A)", len([req for req in yard.tmgr.requests if req.req_type == req.TYPE.ADJUST and req.finish_time > req.start_time])))
    for req_status in ReqStatus:
        print("{:<12}: {}".format(req_status.name, len([req for req in yard.tmgr.requests if req.status == req_status])))

    # for req in yard.tmgr.requests:
    #     if req.status < ReqStatus.FINISHED:
    #         print(req, req.arrival_time)

    print("Finish.")
