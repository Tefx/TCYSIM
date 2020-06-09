from enum import auto, IntEnum
from pickle import dump


class ResultCompareOption(IntEnum):
    NO = auto()
    REAL = auto()
    EXACT = auto()


class Replayable:
    def __init__(self, recorder, func, validate_result):
        self.recorder = recorder
        self.func = func
        self.name = func.__name__
        self.validate_result = validate_result

    def __call__(self, *args, **kwargs):
        if self.recorder.active:
            dump((self.name, args, kwargs), self.recorder.logger)
            res = self.func(self.recorder.yard, *args, **kwargs)
            if self.validate_result != ResultCompareOption.NO:
                dump(res, self.recorder.logger)
            return res
        else:
            return self.func(self.recorder.yard, *args, **kwargs)


class ReqRecoder:
    def __init__(self, enabled=True):
        self.yard = None
        self.logger = None
        self.enabled = enabled
        self.active = False

    def toggle(self, fp=None):
        self.active = not self.active
        if self.active:
            self.logger = fp

    def __call__(self, validate_result=ResultCompareOption.EXACT):
        def wrapper(func):
            if self.enabled:
                return Replayable(self, func, validate_result=validate_result)
            else:
                return func

        return wrapper
