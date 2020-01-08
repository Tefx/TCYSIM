import os
import sys
import random

sys.path.extend([
    "../",
    "../../pesim",
    ])
os.environ['PATH'] = "../libtcy/msvc/Release" + os.pathsep + os.environ['PATH']
os.environ['PATH'] = "../libtcy/cmake-build-debug" + os.pathsep + os.environ['PATH']

from tcysim.implementation.base.policy.allocator import RandomSpaceAllocator
from tcysim.implementation.base.roles.animation_logger import AnimationLogger
from tcysim.implementation.base.roles.box_generator import BoxBomb, BoxGenerator

from tcysim.implementation.scenario.stackingblock.req_handler import CooperativeTwinCraneReqHandler
from tcysim.implementation.scenario.stackingblock.scheduler import CooperativeTwinCraneJobScheduler
from tcysim.implementation.scenario.stackingblock.op_builder import OptimisedOpBuilder
from tcysim.implementation.scenario.stackingblock.block import StackingBlock
from tcysim.implementation.scenario.stackingblock.crane import CraneForStackingBlock

from tcysim.framework import Lane, Component, Spec, Yard, Box, ReqDispatcher, ReqState

from tcysim.utils import V3, TEU


class MultiCraneReqDispatcher(ReqDispatcher):
    def choose_equipment(self, time, request):
        if request.req_type == request.TYPE.STORE and request.lane.name < 5:
            idx = 0
        elif request.req_type == request.TYPE.RELOCATE:
            idx = request.new_loc[0] * self.block.num_equipments // self.block.bays
        else:
            idx = request.box.location[0] * self.block.num_equipments// self.block.bays
        for equipment in self.block.equipments:
            if equipment.idx == idx:
                return equipment


class Block(StackingBlock):
    ReqDispatcher = MultiCraneReqDispatcher


class RMG(CraneForStackingBlock):
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

    ReqHandler = CooperativeTwinCraneReqHandler
    JobScheduler = CooperativeTwinCraneJobScheduler
    OpBuilder = OptimisedOpBuilder


class SimpleYard(Yard):
    SpaceAllocator = RandomSpaceAllocator


from uuid import uuid4


class SimpleBoxBomb(BoxBomb):
    def next_time(self, time):
        return time + random.uniform(300, 600)

    def store_time(self, alloc_time):
        return alloc_time + random.uniform(5, 10)

    def retrieve_time(self, store_time):
        return store_time + random.uniform(3600 * 12, 3600 * 24)

    def new_box(self):
        return Box(str(uuid4())[:8].encode("utf-8"), size=random.choice((20, 40)))


if __name__ == '__main__':
    yard = SimpleYard()

    lanes = [
        Lane(i, V3(0, i * TEU.WIDTH * 2, 0), length=20, width=TEU.WIDTH * 2, rotate=0)
        for i in range(4)
        ]
    lanes.append(Lane(5, V3(25, -TEU.WIDTH * 2, 0), length=TEU.LENGTH * 50, width=TEU.WIDTH * 2, rotate=0))
    lanes.append(Lane(6, V3(25, TEU.WIDTH * 10, 0), length=TEU.LENGTH * 50, width=TEU.WIDTH * 2, rotate=0))
    block = Block(yard, V3(25, 0, 0), V3(16, 10, 6), rotate=0, lanes=lanes)

    rmg1 = RMG(yard, block, 0, idx=0)
    rmg2 = RMG(yard, block, -1, idx=1)
    yard.deploy(block, [rmg1, rmg2])

    # yard.roles.animation_logger = AnimationLogger(yard, start=3600 * 20, end=3600 * 24, fps=24, speedup=10)
    yard.roles.sim_driver = BoxGenerator(yard)
    yard.roles.sim_driver.install_or_add(SimpleBoxBomb(first_time=0))

    yard.start()
    yard.run_until(3600 * 24 * 30)

    if "tracer" in yard.roles:
        yard.roles.animation_logger.dump("log2")

    print("{:<12}: {}".format("TOTAL", len(yard.requests)))
    print("{:<12}: {}".format("TOTAL (AC)", len([req for req in yard.requests if req.finish_time > req.start_time])))
    print("{:<12}: {}".format("TOTAL (NA)", len([req for req in yard.requests if req.req_type != req.TYPE.ADJUST])))
    print("{:<12}: {}".format("TOTAL (A)", len(
        [req for req in yard.requests if req.req_type == req.TYPE.ADJUST and req.finish_time > req.start_time])))
    for req_state in ReqState:
        print("{:<12}: {}".format(req_state.name, len([req for req in yard.requests if req.state == req_state])))

    # for req in yard.requests:
    #     if req.state == req.STATE.READY:
    #         print(req, req.arrival_time, req.cal_start_time, req.finish_time)

    print("Finish.")
