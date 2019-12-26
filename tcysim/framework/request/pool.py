from collections import deque
from .request import Request, ReqStatus


class ReqPool:
    def __init__(self):
        self.free_pool = set()
        self.local_pool = {}
        self.access_queues = {}

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
                        req.predecessor.status >= ReqStatus.STARTED:
                    yield req
