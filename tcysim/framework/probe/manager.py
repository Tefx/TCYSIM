class ProbeManager:
    def __init__(self, yard):
        self._set = {}
        self.yard = yard

    def register(self, probe_name, probe_action):
        if probe_name not in self._set:
            self._set[probe_name] = []
        self._set[probe_name].append(probe_action)

    def fire(self, time, prob_name, *args, **kwargs):
        if prob_name in self._set:
            for action in self._set[prob_name]:
                action.activate(time, args, kwargs)

