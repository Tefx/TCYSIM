from pesim import Process
from ..priority import Priority
from ..request import ReqPool, ReqStatus


class TaskScheduler(Process):
    def __init__(self, yard):
        self.yard = yard
        self.pool = {}
        self.requests = []
        super(TaskScheduler, self).__init__(yard.env)

    def choose_task(self, time, equipment, tasks):
        for task in tasks:
            return task

    def choose_equipment(self, time, request, equipments):
        for equipment in equipments:
            return equipment

    def register_block(self, block):
        self.pool[block] = ReqPool()

    def _process(self):
        self.yard.run_until(self.time)
        self.on_schedule(self.time)

    def schedule(self, time):
        self.activate(time, Priority.SCHEDULE)

    def on_schedule(self, time):
        self.adjust_task_pool(time)
        for equipment in self.yard.equipments:
            if equipment.ready_for_new_task():
                req_or_op = self.next_task_for_equipment(time, equipment)
                if req_or_op is not None:
                    setattr(req_or_op, "time", time)
                    equipment.submit_task(req_or_op)

    def adjust_task_pool(self, time):
        for pool in self.pool.values():
            for request in pool.available_requests():
                if request.status >= ReqStatus.READY:
                    equipment = self.equipment_for_request(time, request)
                    if equipment:
                        pool.repush(request, equipment=equipment)

    def available_tasks_for_equipment(self, time, equipment):
        for block in equipment.blocks:
            for request in self.pool[block].available_requests(equipment):
                if request.status >= ReqStatus.READY:
                    if block.req_handler.validate(time, request):
                        # if request.status == ReqStatus.SENTBACK:
                        #     print("2", request, self.time, request.cb_time, block.req_handler.validate(time, request))
                        yield request

    def available_equipments_for_task(self, time, request):
        if request.equipment:
            yield request.equipment
        else:
            yield from request.block.equipments

    def next_task_for_equipment(self, time, equipment):
        avail_tasks = self.available_tasks_for_equipment(time, equipment)
        request = self.choose_task(time, equipment, avail_tasks)
        if request is not None:
            self.pool[request.block].pop(request)
            return request

    def equipment_for_request(self, time, request):
        if not request.equipment:
            equipments = self.available_equipments_for_task(time, request)
            request.equipment  = self.choose_equipment(time, request, equipments)
        return request.equipment

    def submit_request(self, time, request, ready=True):
        if ready:
            request.ready(time)
        block = request.block
        access_point = request.access_point
        equipment = self.equipment_for_request(time, request)
        self.pool[block].push(request, equipment, access_point)
        self.requests.append(request)
        self.schedule(time)
        return len(self.requests) - 1

    def send_back(self, request):
        block = request.block
        self.pool[block].push(request, request.equipment)

    def get_request(self, handler):
        return self.requests[handler]
