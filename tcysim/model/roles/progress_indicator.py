from pesim import TIME_FOREVER
from pesim.math_aux import time_eq
from tcysim.framework.roles import ObserverBase

try:
    import pandas as pd
except ImportError as e:
    print("ProgressIndicator: need pandas to format datetime")
    raise e


class ProgressIndicator(ObserverBase):
    def __init__(self, yard, interval, start=0, end=TIME_FOREVER, env=None):
        self.sim_start = start
        self._time_zero = pd.to_datetime(yard.ds.TIME_ZERO)
        self.total = end - start
        super(ProgressIndicator, self).__init__(yard=yard, start=start, end=end, interval=interval, env=env)

    def on_observe(self):
        if time_eq(self.end_time, TIME_FOREVER):
            print(pd.Timedelta(self.time, unit="s") + self._time_zero, end="\r")
        else:
            print("[{:.2%}]".format((self.time - self.sim_start) / self.total), pd.Timedelta(self.time, unit="s") + self._time_zero, end="\r")
