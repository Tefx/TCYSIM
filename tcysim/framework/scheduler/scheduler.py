from pesim import Process
from ..priority import Priority


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
            if self.equipment.ready_for_new_task():
                avail_tasks = self.available_requests(time)
                request = self.choose_task(time, avail_tasks)
                if request is not None:
                    # print("schedule", time, request, self.equipment.idx, id(request), getattr(request, "box", None))
                    request.equipment = self.equipment
                    request.block.req_dispatcher.pop_request(request)
                    setattr(request, "time", time)
                    self.equipment.submit_task(request)
            self.pending = False

    def on_idle(self, time):
        return None
