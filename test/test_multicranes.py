import os
import sys
import random

sys.path.extend([
    "../",
    "../../pesim",
    ])
os.environ['PATH'] = "../libtcy/msvc/Release" + os.pathsep + os.environ['PATH']
os.environ['PATH'] = "../libtcy/cmake-build-debug" + os.pathsep + os.environ['PATH']

from tcysim.framework import Lane, Component, Spec, Yard, Box
from tcysim.framework.allocator import SpaceAllocator
from tcysim.framework.scheduler import JobScheduler, ReqDispatcher
from tcysim.framework.request import ReqStatus, Request

from tcysim.implementation.block.stacking_block import StackingBlock
from tcysim.implementation.equipment.crane import Crane
from tcysim.implementation.roles.position_tracer import PositionTracer
from tcysim.implementation.roles.box_generator import BoxBomb, BoxGenerator

from tcysim.utils import V3, TEU


class MultiCraneReqDispatcher(ReqDispatcher):
    def choose_equipment(self, time, request):
        idx = request.box.location[0] * len(self.block.equipments) // self.block.bays
        for equipment in self.block.equipments:
            if equipment.idx == idx:
                return equipment


class Block(StackingBlock):
    ReqDispatcher = MultiCraneReqDispatcher


class CraneJobScheduler(JobScheduler):
    def rank_task(self, request: Request):
        if request.req_type == request.TYPE.ADJUST:
            return 0, request.ready_time
        elif request.status == ReqStatus.RESUME_READY:
            return 1, -request.ready_time
        else:
            return 2, request.ready_time

    def choose_task(self, time, tasks):
        return min(filter(Request.is_ready, tasks), key=self.rank_task, default=None)


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

    JobScheduler = CraneJobScheduler


class RandomSpaceAllocator(SpaceAllocator):
    def alloc_space(self, box, blocks):
        for block in blocks:
            locs = list(block.available_cells(box))
            if locs:
                return block, random.choice(locs)
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


class SimpleYard(Yard):
    SpaceAllocator = RandomSpaceAllocator


class SimpleBoxBomb(BoxBomb):
    def next_time(self, time):
        return time + random.uniform(300, 600)

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
    lanes.append(Lane(5, V3(25, -TEU.WIDTH * 2, 0), length=TEU.LENGTH * 50, width=TEU.WIDTH * 2, rotate=0))
    lanes.append(Lane(6, V3(25, TEU.WIDTH * 8, 0), length=TEU.LENGTH * 50, width=TEU.WIDTH * 2, rotate=0))
    block = Block(yard, V3(25, 0, 0), V3(16, 8, 6), rotate=0, lanes=lanes)

    rmg1 = RMG(yard, block, 0, idx=0)
    rmg2 = RMG(yard, block, -1, idx=1)
    yard.deploy(block, [rmg1, rmg2])

    yard.roles.tracer = PositionTracer(yard, start=3600*20, end=3600*24, interval=1)
    yard.roles.sim_driver = BoxGenerator(yard)
    yard.roles.sim_driver.install_or_add(SimpleBoxBomb(first_time=0))

    yard.start()
    yard.run_until(3600 * 24)

    if "tracer" in yard.roles:
        yard.roles.tracer.dump("log")

    print("{:<12}: {}".format("TOTAL", len(yard.requests)))
    print("{:<12}: {}".format("TOTAL (AC)", len([req for req in yard.requests if req.finish_time > req.start_time])))
    print("{:<12}: {}".format("TOTAL (NA)", len([req for req in yard.requests if req.req_type != req.TYPE.ADJUST])))
    print("{:<12}: {}".format("TOTAL (A)", len(
        [req for req in yard.requests if req.req_type == req.TYPE.ADJUST and req.finish_time > req.start_time])))
    for req_status in ReqStatus:
        print("{:<12}: {}".format(req_status.name, len([req for req in yard.requests if req.status == req_status])))

    # for req in yard.requests:
    #     if req.req_type == req.TYPE.ADJUST:
    #         print(req, req.arrival_time, req.start_time, req.finish_time)

    print("Finish.")