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
    def __init__(self):
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

    def dispatch(self, category, method="_", *args, **kwargs):
        if self is not self._methods[method][category].obj:
            print(self, self._methods[method][category].obj)
            if hasattr(self, "equipment"):
                print(self.equipment.blocks[0].id, self.equipment.idx)
                obj = self._methods[method][category].obj
                print(obj.equipment.blocks[0].id, obj.equipment.idx)
        assert self is self._methods[method][category].obj
        return self._methods[method][category](*args, **kwargs)

    @staticmethod
    def on(category, method="_"):
        def wrapper(func):
            return DispatchFunc(func, category, method)

        return wrapper
