class ProbeAction:
    def __init__(self, prob_name, func):
        self.prob_name = prob_name
        self.func = func
        self.processor = None
        self.time = None
        self.args = None
        self.kwargs = None

    def set_processor(self, processor):
        self.processor = processor

    def activate(self, time, args, kwargs):
        self.time = time
        self.args = args
        self.kwargs = kwargs
        self.processor.add_action(self)

    def __call__(self):
        self.func(self.processor, *self.args, *self.kwargs)

    def __lt__(self, other):
        return self.time < other.time