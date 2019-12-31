from pesim import Process
from ..priority import Priority
from ..request import ReqState
from .pool import ReqPool


class ReqDispatcher:
    def __init__(self, block):
        self.pool = ReqPool()
        self.block = block

    def choose_equipment(self, time, request):
        for equipment in self.block.equipments:
            return equipment

    def available_requests(self, equipment):
        return self.pool.available_requests(equipment)

    def pop_request(self, request):
        return self.pool.pop(request)

    def refresh_pool(self, time):
        for request in self.pool.available_requests():
            if request.state >= ReqState.READY and request.equipment is None:
                if not request.equipment:
                    request.equipment = self.choose_equipment(time, request)
                if request.equipment:
                    self.pool.repush(request, equipment=request.equipment)

    def submit_request(self, time, request):
        access_point = request.access_point
        if not request.equipment:
            request.equipment = self.choose_equipment(time, request)
        self.pool.push(request, request.equipment, access_point)
        if request.equipment:
            request.equipment.job_scheduler.schedule(time)
        else:
            for equipment in self.block.equipments:
                equipment.job_scheduler.schedule(time)


class JobScheduler(Process):
    def __init__(self, equipment):
        self.equipment = equipment
        self.pending = False
        super(JobScheduler, self).__init__(equipment.yard.env)

    def choose_task(self, time, tasks):
        for task in tasks:
            if task.is_ready():
                return task

    @property
    def parent_dispatchers(self):
        for block in self.equipment.blocks:
            yield block.req_dispatcher

    def available_requests(self, time):
        for block in self.equipment.blocks:
            block.req_dispatcher.refresh_pool(time)
            yield from block.req_dispatcher.available_requests(self.equipment)

    def _process(self):
        self.on_schedule(self.time)

    def schedule(self, time):
        self.pending = True
        self.activate(time, Priority.SCHEDULE)

    def on_schedule(self, time):
        if self.pending:
            avail_tasks = self.available_requests(time)
            request = self.choose_task(time, avail_tasks)
            if request is not None:
                request.equipment = self.equipment
                request.block.req_dispatcher.pop_request(request)
                setattr(request, "time", time)
                self.equipment.submit_task(request)
            self.pending = False
