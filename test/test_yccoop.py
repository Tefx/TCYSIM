import os
import sys
import random

from tcysim.framework.equipment.req_handler import ReqHandler
from tcysim.implementation.equipment.op_builder import OptimizedOpBuilder
from tcysim.utils.dispatcher import Dispatcher

sys.path.extend([
    "../",
    "../../pesim",
    ])
os.environ['PATH'] = "../libtcy/msvc/Release" + os.pathsep + os.environ['PATH']
os.environ['PATH'] = "../libtcy/cmake-build-debug" + os.pathsep + os.environ['PATH']

from tcysim.framework import Lane, Component, Spec, Yard, Box
from tcysim.framework.allocator import SpaceAllocator
from tcysim.framework.scheduler import JobScheduler, ReqDispatcher
from tcysim.framework.request import ReqState, Request, ReqType

from tcysim.implementation.block.stacking_block import StackingBlock
from tcysim.implementation.equipment.crane import Crane
from tcysim.implementation.roles.animation_logger import AnimationLogger
from tcysim.implementation.roles.box_generator import BoxBomb, BoxGenerator

from tcysim.utils import V3, TEU


class MultiCraneReqDispatcher(ReqDispatcher):
    def choose_equipment(self, time, request):
        if request.req_type == request.TYPE.STORE and request.lane.name < 5:
            idx = 0
        elif request.req_type == request.TYPE.RELOCATE:
            idx = request.new_loc[0] * len(self.block.equipments) // self.block.bays
        else:
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
        elif hasattr(request, "ph2"):
            return 1, request.ready_time
        elif request.state == ReqState.RESUME_READY:
            return 2, -request.ready_time
        else:
            return 3, request.ready_time

    def choose_task(self, time, tasks):
        return min(filter(Request.is_ready, tasks), key=self.rank_task, default=None)


class Ph2ReqHandler(ReqHandler):
    @Dispatcher.on(ReqType.RETRIEVE)
    def on_request_retrieve(self, time, request):
        if self.equipment.idx == 1 and request.lane.name < 5:
            yield from self.reshuffle_operations(time, request)
            request.ph2 = True
            box = request.box
            start_bay = request.block.bays // 2 - 1
            dst_loc = self.yard.smgr.slot_for_relocation(box, start_bay=start_bay, finish_bay=0)
            if not dst_loc:
                yield None
            if request.acquire_stack(time, box.location, dst_loc):
                yield self.gen_relocate_op(time, request.box, dst_loc, request, reset=False, ph2=True)
            else:
                yield None
        else:
            yield from super(Ph2ReqHandler, self).on_request_retrieve(self, time, request)

    @Dispatcher.on(ReqType.STORE)
    def on_request_store(self, time, request):
        box = request.box
        block = request.block
        if self.equipment.idx == 0 and box.location.x >= block.bays // 2:
            start_bay = request.block.bays // 2 - 1
            dst_loc = self.yard.smgr.slot_for_relocation(box, start_bay=start_bay, finish_bay=0)
            if request.acquire_stack(time, dst_loc):
                request.ph2 = True
                box.final_loc = box.location
                # box.realloc(time, dst_loc)
                box.alloc(time, None, dst_loc)
                request.link_signal("start_or_resume", self.on_store_start, request)
                request.link_signal("off_agv", self.on_store_off_agv, request)
                request.link_signal("in_block", self.on_store_in_block, request)
                request.link_signal("finish_or_fail", self.on_store_finish_or_fail, request)
                yield self.equipment.OpBuilder.StoreOp(request)
            else:
                yield None
        else:
            yield from super(Ph2ReqHandler, self).on_request_store(self, time, request)

    def gen_relocate_op(self, time, box, new_loc, request, reset, ph2=False):
        request.link_signal("rlct_start_or_resume", self.on_relocate_start, box=box, dst_loc=new_loc)
        request.link_signal("rlct_pick_up", self.on_relocate_pickup, box=box, dst_loc=new_loc)
        request.link_signal("rlct_put_down", self.on_relocate_putdown, box=box, dst_loc=new_loc,
                            original_request=request if ph2 else None)
        request.link_signal("rlct_finish_or_fail", self.on_relocate_finish_or_fail, box=box, dst_loc=new_loc)
        return self.equipment.op_builder.RelocateOp(request, box, new_loc, reset=reset)

    def on_relocate_putdown(self, time, box, dst_loc, original_request=None):
        if original_request:
            if original_request.req_type == ReqType.RETRIEVE and getattr(original_request, "ph2", True):
                req2 = Request(self.ReqType.RETRIEVE, time, box, lane=original_request.lane, ph2=True)
                self.yard.submit_request(time, req2)
        super(Ph2ReqHandler, self).on_relocate_putdown(time, box, dst_loc)

    def on_store_in_block(self, time, request):
        if getattr(request, "ph2", False):
            box = request.box
            req2 = Request(self.ReqType.RELOCATE, time, box, new_loc=box.final_loc, ph2=True)
            self.yard.submit_request(time, req2)
        super(Ph2ReqHandler, self).on_store_in_block(time, request)


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

    ReqHandler = Ph2ReqHandler
    JobScheduler = CraneJobScheduler
    OpBuilder = OptimizedOpBuilder


class RandomSpaceAllocator(SpaceAllocator):
    def alloc_space(self, box, blocks, *args, **kwargs):
        for block in blocks:
            locs = list(block.available_cells(box))
            if locs:
                return block, random.choice(locs)
        return None, None

    def slot_for_relocation(self, box, start_bay=None, finish_bay=None):
        i, j, _ = box.location
        block = box.block
        shape = block.shape
        start_bay = i if start_bay is None else start_bay
        finish_bay = i+1 if finish_bay is None else finish_bay
        step = 1 if start_bay < finish_bay else -1
        for i1 in range(start_bay, finish_bay, step):
            for j1 in range(0, shape.y):
                if (i1, j1) != (i, j):
                    k = block.count(i1, j1)
                    if block.stack_is_valid(box, i1, j1):
                        return V3(i1, j1, k)


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
    lanes.append(Lane(6, V3(25, TEU.WIDTH * 10, 0), length=TEU.LENGTH * 50, width=TEU.WIDTH * 2, rotate=0))
    block = Block(yard, V3(25, 0, 0), V3(26, 10, 6), rotate=0, lanes=lanes)

    rmg1 = RMG(yard, block, 0, idx=0)
    rmg2 = RMG(yard, block, -1, idx=1)
    yard.deploy(block, [rmg1, rmg2])

    # yard.roles.tracer = AnimationLogger(yard, start=3600 * 20, end=3600 * 24, fps=24, speedup=10)
    yard.roles.sim_driver = BoxGenerator(yard)
    yard.roles.sim_driver.install_or_add(SimpleBoxBomb(first_time=0))

    yard.start()
    yard.run_until(3600 * 24 * 30)

    if "tracer" in yard.roles:
        yard.roles.tracer.dump("log2")

    print("{:<12}: {}".format("TOTAL", len(yard.requests)))
    print("{:<12}: {}".format("TOTAL (AC)", len([req for req in yard.requests if req.finish_time > req.start_time])))
    print("{:<12}: {}".format("TOTAL (NA)", len([req for req in yard.requests if req.req_type != req.TYPE.ADJUST])))
    print("{:<12}: {}".format("TOTAL (A)", len(
        [req for req in yard.requests if req.req_type == req.TYPE.ADJUST and req.finish_time > req.start_time])))
    for req_state in ReqState:
        print("{:<12}: {}".format(req_state.name, len([req for req in yard.requests if req.state == req_state])))

    # for req in yard.requests:
    #     if req.state == req.STATE.READY:
    #         print(req, req.arrival_time, req.start_time, req.finish_time)

    print("Finish.")
