from pesim import Environment
from .env import YardEnv
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
        self.requests = []

        self.smgr = self.SpaceAllocator(self)
        self.cmgr = CallBackManager(self)

        self.roles = Roles()
        self.movers = []

    def add_role(self, name, role):
        self.roles[name] = role

    def deploy(self, block, equipments):
        self.blocks.add(block)
        block.deploy(equipments)

        self.smgr.register_block(block)

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

    def add_request(self, request):
        if request.id == -1:
            request.id = len(self.requests)
            self.requests.append(request)
            return request.id

    def get_request(self, handler):
        return self.requests[handler]

    def submit_request(self, time, request, ready=True):
        # print("submit_x", id(request), getattr(request, "box", None))
        if request.req_type == request.TYPE.RETRIEVE and request.box.state == request.box.STATE.RETRIEVED:
            raise Exception("here!")
        request.submit(time, ready)
        return self.add_request(request)

    def query_request_state(self, time, handler):
        request = self.get_request(handler)
        time = self.env.run_until(time, proc_next=request.equipment)
        return request.state, time

    def alloc(self, time, box):
        block, loc = self.smgr.alloc_space(box, self.smgr.available_blocks(box))
        if not loc:
            return False
        box.alloc(time, block, loc)
        return True

    def store(self, time, box, lane):
        request = Request(ReqType.STORE, time, box, lane=lane)
        return self.submit_request(time, request)

    def retrieve(self, time, box, lane):
        request = Request(ReqType.RETRIEVE, time, box, lane=lane)
        return self.submit_request(time, request)

    def run_until(self, time):
        self.env.run_until(time)
        self.run_equipments(time)

    def run_equipments(self, time):
        for equipment in self.equipments:
            equipment.run_until(time)

