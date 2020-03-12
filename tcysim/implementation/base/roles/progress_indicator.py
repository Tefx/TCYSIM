from pesim import TIME_FOREVER
from tcysim.framework.roles import Observer
import pandas as pd


class ProgressIndicator(Observer):
    def __init__(self, ds, yard, interval, end=TIME_FOREVER, env=None):
        start = (pd.to_datetime(ds.FIRST_BOX_TIME) - pd.to_datetime(ds.TIME_ZERO)).total_seconds()
        self._start = start
        self._time_zero = pd.to_datetime(ds.TIME_ZERO)
        self.total = end - start
        super(ProgressIndicator, self).__init__(yard=yard, start=start, end=end, interval=interval, env=env)

    def on_observe(self):
        if self.end == TIME_FOREVER:
            print(pd.Timedelta(self.time, unit="s") + self._time_zero, end="\r")
        else:
            print("[{:.2%}]".format((self.time - self._start) / self.total), pd.Timedelta(self.time, unit="s") + self._time_zero, end="\r")
