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
        print(time)
        self.yard.run_until(time, run_env=False)


class Yard:
    SpaceAllocator: SpaceAllocator.__class__ = SpaceAllocator
    TaskScheduler: TaskScheduler.__class__ = TaskScheduler
    Observer: Observer.__class__ = Observer

    def __init__(self):
        self.env = Environment()
        self.blocks = set()
        self.equipments = set()
        self.boxes = set()

        self.smgr = self.SpaceAllocator(self)
        self.tmgr = self.TaskScheduler(self)
        self.cmgr = CallBackManager(self.env)
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
        self.env.run_until(time)
        handler = self.tmgr.submit_request(self.env.current_time, request)
        return handler

    def query_request_status(self, time, handler):
        request = self.tmgr.get_request(handler)
        time = self.env.run_until(time, proc_next=request.equipment)
        return request.status, time

    def alloc(self, time, box):
        self.run_until(time)
        block, loc = self.smgr.alloc_space(box, self.smgr.available_blocks(box))
        if not loc:
            return False
        else:
            box.set_location(block, *loc)
            box.alloc(time)
            return True

    def choose_slot_for_reshuffle(self, time, box):
        self.run_until(time)
        return self.smgr.slot_for_reshuffle(box)

    def store_off_agv(self, time, request):
        box = request.box
        box.state = box.STATE_STORING
        request.sync(time)
        box.equipment = request.equipment
        self.boxes.add(box)
        # print("ADD", box)

    def store_on_block(self, time, request, ):
        box = request.box
        # request.box.store(time)
        box.state = box.STATE_STORED
        # print(box, "Stored")
        box.block.unlock(box.location)
        box.equipment = None

    def retrieve_off_block(self, time, request):
        box = request.box
        # box.state = request.box.STATE_RETRIEVING
        box.block.unlock(box.location)
        box.equipment = request.equipment

    def retrieve_on_agv(self, time, request):
        box = request.box
        # box.retrieve(time)
        if box not in self.boxes:
            print(request)
        box.state = box.STATE_RETRIEVING
        request.sync(time)
        box.equipment = None
        self.boxes.remove(box)
        # print("REMOVE", box)

    def reshuffle_pickup(self, time, box, equipment, dst_loc):
        box.equipment = equipment
        box.block.unlock(box.previous_loc)

    def reshuffle_putdown(self, time, box):
        box.block.lock(box.location)
        box.state = box.STATE_STORED
        box.equipment = None

    def store(self, time, box, lane):
        self.run_until(time)
        request = box.block.ReqHandler.StoreRequest(time, box, lane)
        request.link_signal("off_agv", self.store_off_agv, request)
        request.link_signal("on_block", self.store_on_block, request)
        return self.submit_request(time, request)

    def retrieve(self, time, box, lane):
        self.run_until(time)
        request = box.block.ReqHandler.RetrieveRequest(time, box, lane)
        request.link_signal("off_block", self.retrieve_off_block, request)
        request.link_signal("on_agv", self.retrieve_on_agv, request)
        return self.submit_request(time, request)

    def run_until(self, time, run_env=True):
        if run_env:
            self.env.run_until(time)
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
