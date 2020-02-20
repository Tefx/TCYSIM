from pesim import Process, TIME_FOREVER, MinPairingHeap
from tcysim.framework.priority import Priority
from tcysim.framework.probe.action import ProbeActionTemplate


class ProbeProcessor(Process):
    def __init__(self, yard):
        super(ProbeProcessor, self).__init__(yard.env)
        self.yard = yard
        self.probe_mgr = self.yard.probe_mgr
        self.actions = MinPairingHeap()
        for name in dir(self):
            item = getattr(self, name)
            if isinstance(item, ProbeActionTemplate):
                self.probe_mgr.register(item)
                item.set_processor(self)

    def _wait(self, priority=Priority.PROBE):
        action = self.actions.first()
        if action:
            return action.time, priority
        else:
            return TIME_FOREVER, priority

    def _process(self):
        self.actions.pop()()

    def add_action(self, action):
        self.actions.push(action)
        self.activate(action.time, Priority.PROBE)