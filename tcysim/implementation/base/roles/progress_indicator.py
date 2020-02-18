from tcysim.framework.roles import Observer
import pandas as pd


class ProgressIndicator(Observer):
    def __init__(self, ds, yard, interval, end=None, env=None):
        start = (pd.to_datetime(ds.FIRST_BOX_TIME) - pd.to_datetime(ds.TIME_ZERO)).total_seconds()
        end = end or (pd.to_datetime(ds.END_TIME) - pd.to_datetime(ds.TIME_ZERO)).total_seconds()
        self.ds = ds
        self.start = start
        self.total = end - start
        super(ProgressIndicator, self).__init__(yard=yard, start=start, end=end, interval=interval, env=env)

    def on_observe(self):
        print("[{:.2%}]".format((self.time - self.start) / self.total), pd.Timedelta(self.time, unit="s") + pd.to_datetime(self.ds.TIME_ZERO), end="\r")
