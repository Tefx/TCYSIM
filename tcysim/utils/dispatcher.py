class DispatchFunc:
    def __init__(self, func, category, method):
        self.func = func
        self.category = category.name
        self.method = method

    def __call__(self, *args, **kwargs):
        # print(self.func, *args, **kwargs)
        return self.func(*args, **kwargs)
        # print("DONE", self.func)
        # return res

class Dispatcher:
    def __init__(self):
        self._methods = {}
        for item in dir(self):
            item = getattr(self, item)
            if isinstance(item, DispatchFunc):
                if item.method not in self._methods:
                    self._methods[item.method] = {}
                self._methods[item.method][item.category] = item

    def dispatch(self, category, method="_", *args, **kwargs):
        return self._methods[method][category.name](self, *args, **kwargs)

    @staticmethod
    def on(category, method="_"):
        def wrapper(func):
            return DispatchFunc(func, category, method)
        return wrapper
