from pesim import Process, TIME_FOREVER, MinPairingHeap
from tcysim.framework.event_reason import EventReason
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

    def _wait(self):
        action = self.actions.first()
        if action:
            return action.time, EventReason.PROBE_ACTION
        else:
            return TIME_FOREVER, EventReason.LAST

    def _process(self):
        self.actions.pop()()

    def add_action(self, action):
        self.actions.push(action)
        self.activate(action.time, EventReason.PROBE_ACTION)