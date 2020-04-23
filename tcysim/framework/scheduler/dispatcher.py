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
            if request.state >= request.STATE.READY and request.equipment is None:
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