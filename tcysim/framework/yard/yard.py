from pesim import Environment
from .env import YardEnv
from ..probe import ProbeManager
from ..request import ReqType, Request
from ..roles import Roles
from ..callback import CallBackManager
from ..allocator import SpaceAllocator


class Yard:
    SpaceAllocator: SpaceAllocator.__class__ = SpaceAllocator

    def __init__(self):
        # self.env = YardEnv(self)
        self.env = Environment()
        self.blocks = set()
        self.equipments = set()

        self.boxes = set()
        # self.requests = []

        self.smgr = self.SpaceAllocator(self)
        self.cmgr = CallBackManager(self)
        self.probe_mgr = ProbeManager(self)

        self.roles = Roles()
        self.movers = []

    def deploy(self, block, equipments):
        self.blocks.add(block)
        block.deploy(equipments)

        for equipment in equipments:
            self.equipments.add(equipment)
            for component in equipment.components:
                self.movers.append(component)

    def start(self):
        self.cmgr.setup()

        for equipment in self.equipments:
            equipment.setup()

        self.roles.setup()

        self.env.start()

    def finish(self):
        self.roles.finish()

    # def add_request(self, request):
    #     if request.id == -1:
    #         request.id = len(self.requests)
    #         self.requests.append(request)
    #         return request.id

    def fire_probe(self, probe_name, *args, **kwargs):
        return self.probe_mgr.fire(self.env.current_time, probe_name, *args, **kwargs)

    # def get_request(self, handler):
    #     return self.requests[handler]

    def submit_request(self, time, request, ready=True):
        if request.req_type == request.TYPE.RETRIEVE and request.box.state == request.box.STATE.RETRIEVED:
            raise Exception("here!")
        request.submit(time, ready)

    def query_request_state(self, time, handler):
        request = self.get_request(handler)
        time = self.env.run_until(time, proc_next=request.equipment)
        return request.state, time

    def choose_location(self, box):
        return self.smgr.alloc_space(box, self.smgr.available_blocks(box))

    def alloc(self, time, box, block, loc):
        box.alloc(time, block, loc)

    def store(self, time, box, lane):
        request = Request(ReqType.STORE, time, box, lane=lane)
        self.submit_request(time, request)
        return request

    def retrieve(self, time, box, lane):
        request = Request(ReqType.RETRIEVE, time, box, lane=lane)
        self.submit_request(time, request)
        return request

    def run_until(self, time):
        self.env.run_until(time)
        self.run_equipments(time)

    def run_equipments(self, time):
        for equipment in self.equipments:
            equipment.run_until(time)

