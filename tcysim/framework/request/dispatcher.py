from collections import deque


class ReqPool:
    def __init__(self):
        self.free_pool = set()
        self.local_pool = {}
        self.access_queues = {}

    def all_requests(self):
        yield from self.free_pool
        for pool in self.local_pool.values():
            yield from pool
        for queue in self.access_queues.values():
            yield from queue

    def push(self, request, equipment=None, access_name=None):
        if equipment is not None:
            if equipment not in self.local_pool:
                self.local_pool[equipment] = set()
            self.local_pool[equipment].add(request)
            request.queue = equipment
        elif access_name is not None:
            if access_name not in self.access_queues:
                self.access_queues[access_name] = deque()
            queue = self.access_queues[access_name]
            if queue:
                request.predecessor = queue[-1]
            else:
                request.predecessor = None
            queue.append(request)
            request.queue = access_name
        else:
            self.free_pool.add(request)
            request.queue = "free"

    def pop(self, request):
        if not hasattr(request, "queue"):
            import pdb
            pdb.set_trace()
        if request.queue == "free":
            self.free_pool.remove(request)
        elif isinstance(request.queue, str) or isinstance(request.queue, int):
            self.access_queues[request.queue].popleft()
        else:
            self.local_pool[request.queue].remove(request)
        del request.queue

    def repush(self, request, equipment):
        self.push(self.pop(request), equipment)

    def available_requests(self, equipment=None):
        if equipment in self.local_pool:
            yield from self.local_pool[equipment]
        yield from self.free_pool
        for queue in self.access_queues.values():
            if queue:
                req = queue[0]
                if req.predecessor is None or \
                        req.predecessor.state == req.STATE.FINISHED:
                    yield req


class ReqDispatcher:
    def __init__(self, block):
        self.pool = ReqPool()
        self.block = block

    def choose_equipment(self, time, request):
        return None
        # for equipment in self.block.equipments:
        #     return equipment

    def available_requests(self, equipment):
        return self.pool.available_requests(equipment)

    def pop_request(self, request):
        return self.pool.pop(request)

    def push_request(self, request):
        self.pool.push(request, request.equipment, request.access_point)

    def refresh_pool(self, time):
        requests = tuple(self.pool.available_requests())
        for request in requests:
            if request.state & request.STATE.READY_FLAG:
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

    def schedule(self, time, request):
        if request.equipment:
            request.equipment.job_scheduler.schedule(time)
        else:
            for equipment in self.block.equipments:
                equipment.job_scheduler.schedule(time)
