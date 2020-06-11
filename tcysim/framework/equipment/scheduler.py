from pesim import Process
from ..event_reason import EventReason


class JobScheduler(Process):
    def __init__(self, equipment):
        self.equipment = equipment
        self.pending = False
        self.yard = equipment.yard
        super(JobScheduler, self).__init__(equipment.yard.env)

    def rank_task(self, request):
        return request.ready_time

    def choose_task(self, time, tasks):
        min_rank = None
        chosen = None
        for task in tasks:
            if task.is_ready():
                rank = self.rank_task(task)
                if min_rank is None or rank < min_rank:
                    chosen = task
                    min_rank = rank
        return chosen

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

    def schedule(self, time, reason=EventReason.SCHEDULE):
        self.pending = True
        self.activate(time, reason)

    def on_schedule(self, time):
        if self.pending:
            if self.equipment.ready_for_new_task():
                avail_tasks = self.available_requests(time)
                request = self.choose_task(time, avail_tasks)
                if request is not None:
                    request.equipment = self.equipment
                    request.block.req_dispatcher.pop_request(request)
                    setattr(request, "time", time)
                    self.equipment.submit_task(request)
                    self.yard.fire_probe(self.time, 'scheduler.scheduled', request)
            self.pending = False

    def on_idle(self, time):
        return None
