import heapq

from pesim import Process
from tcysim.framework.priority import Priority
from tcysim.framework.probe.action import ProbeAction


class ProbeProcessor(Process):
    def __init__(self, yard):
        super(ProbeProcessor, self).__init__(yard.env)
        self.yard = yard
        self.probe_mgr = self.yard.probe_mgr
        self.actions = []
        for name in dir(self):
            item = getattr(self, name)
            if isinstance(item, ProbeAction):
                self.probe_mgr.register(item.prob_name, item)
                item.set_processor(self)

    def _process(self):
        heapq.heappop(self.actions)()

    def add_action(self, action):
        heapq.heappush(self.actions, action)
        self.activate(action.time, Priority.PROBE)