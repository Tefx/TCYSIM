from pesim import Environment, TIME_PASSED
from ..event_reason import EventReason
from ..probe import ProbeManager
from ..request import Request
from ..roles import Roles
from ..callback import CallBackManager
from ..allocator import SpaceAllocator


class Yard:
    SpaceAllocator: SpaceAllocator.__class__ = SpaceAllocator
    ReqCls = Request

    def __init__(self):
        self.env = Environment()
        self.blocks = {}
        self.equipments = []

        self.smgr = self.SpaceAllocator(self)
        self.cmgr = CallBackManager(self)
        self.probe_mgr = ProbeManager(self)

        self.roles = Roles()
        self.movers = []

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

    def start(self):
        self.env.start()

    def finish(self):
        self.env.finish()

    def run_until(self, time, after_reason=TIME_PASSED):
        return self.env.run_until(time, after_reason)

    def fire_probe(self, probe_name, *args, **kwargs):
        return self.probe_mgr.fire(self.env.time, probe_name, args, kwargs, EventReason.PROBE_ACTION)

    def submit_request(self, time, request, ready=True):
        request.submit(time, ready)

    def choose_location(self, box):
        return self.smgr.alloc_space(box, self.smgr.available_blocks(box))

    def alloc(self, time, box, block, loc):
        box.alloc(time, block, loc)
        self.fire_probe("box.alloc", box)

    def store(self, time, box, lane):
        request = self.new_request("STORE", time, box, lane=lane)
        self.submit_request(time, request)
        return request

    def retrieve(self, time, box, lane):
        request = self.new_request("RETRIEVE", time, box, lane=lane)
        self.submit_request(time, request)
        return request

    @classmethod
    def new_request(cls, type, *args, **kwargs):
        return cls.ReqCls(cls.ReqCls.TYPE[type], *args, **kwargs)

    def boxes(self):
        for block in self.blocks:
            yield from block.iterboxes()
