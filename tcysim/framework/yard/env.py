from pesim import Environment


class YardEnv(Environment):
    def __init__(self, yard):
        super(YardEnv, self).__init__()
        self.yard = yard
        self.last_time = -1

    def pre_ev_hook(self, time):
        if time > self.last_time:
            self.yard.run_equipments(time)
            self.last_time = time