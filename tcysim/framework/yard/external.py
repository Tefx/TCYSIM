from pesim import Environment, TIME_PASSED
from tcysim.framework.roles import Roles


class ExternalDriver:
    EventGenerator = NotImplemented

    def __init__(self, yard, stop_time, start_from=0, ev_gen_args={}):
        self.env = Environment()
        self.roles = Roles()
        self.roles.ev_gen = self.EventGenerator(yard, start_from, stop_time=stop_time, env=self.env, **ev_gen_args)
        self.yard = yard
        self.start_from = start_from

    def start(self):
        self.env.start()
        self.yard.start()

        if self.start_from > 0:
            self.run_until(self.start_from)

    def run_until(self, time, after_reason=TIME_PASSED):
        time = self.env.run_until(time, after_reason)
        self.yard.run_until(time, after_reason)
        return time

    def finish(self):
        self.env.finish()
        self.yard.finish()

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.finish()
