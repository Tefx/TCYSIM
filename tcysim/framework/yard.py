from pesim import Environment
from .generator import Generator
from .observer import Observer
from .callback import CallBackManager
from .request import Request
from .management import SpaceAllocator, TaskScheduler


class YardEnv(Environment):
    def __init__(self, yard):
        self.yard = yard
        super(YardEnv, self).__init__()
        
    def pre_ev_hook(self, time):
        self.yard.run_equipments(time)

class Yard:
    SpaceAllocator: SpaceAllocator.__class__ = SpaceAllocator
    TaskScheduler: TaskScheduler.__class__ = TaskScheduler
    Observer: Observer.__class__ = Observer

    def __init__(self):
        # self.env = Environment()
        self.env = YardEnv(self)
        self.blocks = set()
        self.equipments = set()

        self.boxes = set()

        self.smgr = self.SpaceAllocator(self)
        self.tmgr = self.TaskScheduler(self)
        self.cmgr = CallBackManager(self)
        self.observer = None
        self.generator = None

    def install_observer(self, Observer, *args, **kwargs):
        self.observer = Observer(self, *args, **kwargs)

    def install_generator(self, Bomb, *args, **kwargs):
        if not self.generator:
            self.generator = Generator(self)
        self.generator.install_or_add(Bomb(*args, **kwargs))

    def deploy(self, block, equipments):
        self.blocks.add(block)
        block.deploy(equipments)

        self.smgr.register_block(block)
        self.tmgr.register_block(block)

        for equipment in equipments:
            self.equipments.add(equipment)

    def start(self):
        self.tmgr.setup()
        self.cmgr.setup()

        for equipment in self.equipments:
            equipment.setup()

        if self.generator:
            self.generator.setup()

        if self.observer:
            self.observer.setup()

        self.env.start()

    def submit_request(self, time, request):
        # self.run_until2(time)
        handler = self.tmgr.submit_request(time, request)
        return handler

    def query_request_status(self, time, handler):
        request = self.tmgr.get_request(handler)
        time = self.env.run_until(time, proc_next=request.equipment)
        return request.status, time

    def alloc(self, time, box):
        # self.run_until2(time)
        block, loc = self.smgr.alloc_space(box, self.smgr.available_blocks(box))
        return box.alloc(time, block, loc)

    def store(self, time, box, lane):
        # self.run_until2(time)
        req_builder = box.block.req_builder
        request = req_builder(req_builder.ReqType.STORE, time, box, lane)
        return self.submit_request(time, request)

    def retrieve(self, time, box, lane):
        # self.run_until2(time)
        req_builder = box.block.req_builder
        request = req_builder(req_builder.ReqType.RETRIEVE, time, box, lane)
        return self.submit_request(time, request)

    def run_until(self, time):
        self.env.run_until(time)
        self.run_equipments(time)

    def run_equipments(self, time):
        for equipment in self.equipments:
            equipment.run_until(time)

    def equipment_coords(self):
        for equipment in self.equipments:
            yield equipment, equipment.coord()

    def box_coords(self):
        for box in self.boxes:
            coord = box.coord()
            if coord:
                yield box, coord
