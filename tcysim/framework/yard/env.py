from pesim import Environment


class YardEnv(Environment):
    def __init__(self, yard):
        self.yard = yard
        super(YardEnv, self).__init__()

    def pre_ev_hook(self, time):
        self.yard.run_equipments(time)