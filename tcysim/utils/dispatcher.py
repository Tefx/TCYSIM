from copy import copy
from enum import Enum


class DispatchFunc:
    __slots__ = ["func", "category", "method", "obj"]
    def __init__(self, func, category, method):
        self.func = func
        if isinstance(category, str):
            self.category = category
        elif isinstance(category, Enum):
            self.category = category.name
        self.method = method
        self.obj = None

    def __call__(self, *args, **kwargs):
        return self.func(self.obj, *args, **kwargs)

    def call(self, obj, *args, **kwargs):
        return self.func(obj, *args, **kwargs)


class Dispatcher:
    def __init__(self, *args, **kwargs):
        super(Dispatcher, self).__init__(*args, **kwargs)
        self._methods = {}
        for item_name in dir(self):
            item = getattr(self, item_name)
            if isinstance(item, DispatchFunc):
                if item.method not in self._methods:
                    self._methods[item.method] = {}
                item = copy(item)
                item.obj = self
                setattr(self, item_name, item)
                self._methods[item.method][item.category] = item

    def dispatch(self, category, method, *args, **kwargs):
        assert self is self._methods[method][category].obj
        return self._methods[method][category](*args, **kwargs)

    def dispatch_if_registered(self, category, method, default_func, *args, **kwargs):
        if method in self._methods:
            if category in self._methods[method]:
                return self._methods[method][category](*args, **kwargs)
        if default_func is not None:
            return default_func(*args, **kwargs)

    @staticmethod
    def on(category, method="_"):
        def wrapper(func):
            return DispatchFunc(func, category, method)
        return wrapper
