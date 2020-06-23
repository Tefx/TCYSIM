from abc import ABC

from typing import Type
from pesim import Environment, TIME_PASSED
from .access import AccessPoint
from ..event_reason import EventReason
from ..probe import ProbeManager
from ..roles import Roles
from ..callback import CallBackManager
from ..allocator import SpaceAllocatorBase


class YardBase(ABC):
    SpaceAllocatorCls: Type[SpaceAllocatorBase] = NotImplemented

    def __init__(self):
        self.env = Environment()
        self.blocks = {}
        self.equipments = []

        self.smgr = self.SpaceAllocatorCls(self)
        self.cmgr = CallBackManager(self)
        self.probe_mgr = ProbeManager(self)

        self.roles = Roles()
        self.movers = []

        self.access_points = {}

    @property
    def time(self):
        return self.env.time

    def deploy(self, block, equipments):
        self.blocks[block.id] = block
        block.deploy(equipments)

        for equipment in equipments:
            if equipment not in self.equipments:
                self.equipments.append(equipment)
                for component in equipment.components:
                    self.movers.append(component)

    def deploy_access_point(self, block, lane, access_point=None):
        if access_point is None:
            access_point = AccessPoint(self.env)
        self.access_points[(block, lane)] = access_point

    def start(self, request_pool_size=10240):
        self.env.start()

    def finish(self):
        self.env.finish()

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.finish()

    def run_until(self, time, after_reason=TIME_PASSED):
        return self.env.run_until(time, after_reason)

    def fire_probe(self, probe_name, *args, **kwargs):
        return self.probe_mgr.fire(self.env.time, probe_name, args, kwargs, EventReason.PROBE_ACTION)

    # def submit_request(self, time, request, ready=True):
    #     request.submit(time, ready)

    def choose_location(self, box):
        return self.smgr.alloc_space(box, self.smgr.available_blocks(box))

    def alloc(self, time, box, block, loc):
        box.alloc(time, block, loc)
        self.fire_probe("box.alloc", box)

    def store(self, time, box, lane):
        request = box.block.new_request("STORE", time, box, lane=lane)
        ap = self.access_points.get((box.block, lane), None)
        if ap is None:
            request.submit(time)
        else:
            ap.submit(time, request)
        return request

    def retrieve(self, time, box, lane):
        request = box.block.new_request("RETRIEVE", time, box, lane=lane)
        ap = self.access_points.get((box.block, lane), None)
        if ap is None:
            request.submit(time)
        else:
            ap.submit(time, request)
        return request

    def boxes(self):
        for block in self.blocks:
            yield from block.iterboxes()

