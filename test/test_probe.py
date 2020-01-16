import os
import sys
import random

from tcysim.utils.dispatcher import Dispatcher

sys.path.extend([
    "../",
    "../../pesim",
    ])
os.environ['PATH'] = "../libtcy/msvc/Release" + os.pathsep + os.environ['PATH']
os.environ['PATH'] = "../libtcy/cmake-build-debug" + os.pathsep + os.environ['PATH']

from tcysim.implementation.scenario.stackingblock.allocator import RandomSpaceAllocator
from tcysim.implementation.base.roles.box_generator import BoxBomb, BoxGenerator
from tcysim.implementation.scenario.stackingblock.scheduler import CooperativeTwinCraneJobScheduler
from tcysim.implementation.scenario.stackingblock.op_builder import OptimisedOpBuilder
from tcysim.implementation.scenario.stackingblock.block import StackingBlock
from tcysim.implementation.scenario.stackingblock.crane import CraneForStackingBlock

from tcysim.framework.exception.handling import RORUndefinedError
from tcysim.framework.probe import ProbeProcessor, on_probe
from tcysim.implementation.base.policy.req_handler import ReqHandler

from tcysim.implementation.base.roles.animation_logger import AnimationLogger
from tcysim.framework import Lane, Component, Spec, Yard, Box, ReqDispatcher, ReqState, ReqType, Request

from tcysim.utils import V3, TEU


class MultiCraneReqDispatcher(ReqDispatcher):
    def choose_equipment(self, time, request):
        if request.req_type == request.TYPE.STORE and request.lane.name < 5:
            idx = 0
        elif request.req_type == request.TYPE.RELOCATE:
            idx = request.new_loc[0] * self.block.num_equipments // self.block.bays
        else:
            idx = request.box.location[0] * self.block.num_equipments // self.block.bays
        for equipment in self.block.equipments:
            if equipment.idx == idx:
                return equipment


class Block(StackingBlock):
    ReqDispatcher = MultiCraneReqDispatcher


class CooperativeTwinCraneReqHandler(ReqHandler):
    @Dispatcher.on(ReqType.RETRIEVE)
    def on_request_retrieve(self, time, request):
        if self.equipment.idx == 1 and request.lane.name < 5:
            yield from self.reshuffle_operations(time, request)
            request.coop_flag = True
            box = request.box
            start_bay = request.block.bays // 2 - 1
            dst_loc = self.yard.smgr.slot_for_relocation(box, start_bay=start_bay, finish_bay=0)
            if not dst_loc:
                raise RORUndefinedError("no slot for relocation")
            request.acquire_stack(time, box.location, dst_loc)
            yield self.gen_relocate_op(time, request.box, dst_loc, request, coop_flag=True)
        else:
            yield from super(CooperativeTwinCraneReqHandler, self).on_request_retrieve(self, time, request)

    @Dispatcher.on(ReqType.STORE)
    def on_request_store(self, time, request):
        box = request.box
        block = request.block
        if self.equipment.idx == 0 and box.location.x >= block.bays // 2:
            start_bay = request.block.bays // 2 - 1
            dst_loc = self.yard.smgr.slot_for_relocation(box, start_bay=start_bay, finish_bay=0)
            if not dst_loc:
                raise RORUndefinedError("no slot for relocation")
            request.acquire_stack(time, dst_loc)
            request.coop_flag = True
            request.dst_loc = dst_loc
            request.link_signal("start_or_resume", self.on_store_start, request)
            request.link_signal("off_agv", self.on_store_off_agv, request)
            request.link_signal("in_block", self.on_store_in_block, request)
            request.link_signal("finish_or_fail", self.on_store_finish_or_fail, request)
            yield self.equipment.OpBuilder.StoreOp(request)
        else:
            yield from super(CooperativeTwinCraneReqHandler, self).on_request_store(self, time, request)

    def gen_relocate_op(self, time, box, new_loc, request, coop_flag=False):
        request.link_signal("rlct_start_or_resume", self.on_relocate_start, box=box, dst_loc=new_loc)
        request.link_signal("rlct_pick_up", self.on_relocate_pickup, box=box)
        request.link_signal("rlct_put_down", self.on_relocate_putdown, box=box,
                            original_request=request if coop_flag else None)
        request.link_signal("rlct_finish_or_fail", self.on_relocate_finish_or_fail, box=box)
        return self.equipment.op_builder.RelocateOp(request, box, new_loc)

    def on_relocate_putdown(self, time, box, original_request=None):
        super(CooperativeTwinCraneReqHandler, self).on_relocate_putdown(time, box)
        if original_request:
            if original_request.req_type == ReqType.RETRIEVE and getattr(original_request, "ph2", True):
                req2 = Request(self.ReqType.RETRIEVE, time, box, lane=original_request.lane, coop_flag=True)
                self.yard.submit_request(time, req2)

    def on_store_start(self, time, request):
        if getattr(request, "coop_flag", False):
            box = request.box
            box.final_loc = box.location
            box.alloc(time, None, request.dst_loc)
        super(CooperativeTwinCraneReqHandler, self).on_store_start(time, request)

    def on_store_in_block(self, time, request):
        if getattr(request, "coop_flag", False):
            box = request.box
            req2 = Request(self.ReqType.RELOCATE, time, box, new_loc=box.final_loc, coop_flag=True)
            self.yard.submit_request(time, req2)
        super(CooperativeTwinCraneReqHandler, self).on_store_in_block(time, request)


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
        return time + random.uniform(30, 60)

    def store_time(self, alloc_time):
        return alloc_time + random.uniform(5, 10)

    def retrieve_time(self, store_time):
        return store_time + random.uniform(3600 * 12, 3600 * 24)

    def new_box(self):
        return Box(str(uuid4())[:8].encode("utf-8"), size=random.choice((20, 40)))


from tcysim.implementation import probe


class SimpleProbeProcessor(ProbeProcessor):
    on_op_start = on_probe("operation.start")(probe.operation.print_on_start)
    on_op_finish = on_probe("operation.finish")(probe.operation.print_on_finish_or_fail)
    on_req_start = on_probe("request.start")(probe.request.print_status)
    on_req_finish = on_probe("request.succeed")(probe.request.print_status)
    on_req_fail = on_probe("request.rejected")(probe.request.print_status)


if __name__ == '__main__':
    yard = SimpleYard()

    lanes = [
        # Lane(i, V3(0, i * TEU.WIDTH * 2, 0), length=20, width=TEU.WIDTH * 2, rotate=0)
        # for i in range(4)
        ]
    lanes.append(Lane(5, V3(25, -TEU.WIDTH * 2, 0), length=TEU.LENGTH * 50, width=TEU.WIDTH * 2, rotate=0))
    lanes.append(Lane(6, V3(25, TEU.WIDTH * 10, 0), length=TEU.LENGTH * 50, width=TEU.WIDTH * 2, rotate=0))
    block = Block(yard, V3(25, 0, 0), V3(52, 10, 6), rotate=0, lanes=lanes)

    rmg1 = RMG(yard, block, 0, idx=0)
    rmg2 = RMG(yard, block, -1, idx=1)
    yard.deploy(block, [rmg1, rmg2])

    # yard.roles.animation_logger = AnimationLogger(yard, start=3600 * 20, end=3600 * 21, fps=24, speedup=10)
    yard.roles.sim_driver = BoxGenerator(yard)
    yard.roles.sim_driver.install_or_add(SimpleBoxBomb(first_time=0))

    yard.roles.probe1 = SimpleProbeProcessor(yard)

    yard.start()
    yard.run_until(3600 * 24 * 30)

    if "animation_logger" in yard.roles:
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
