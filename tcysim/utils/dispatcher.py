class Dispatcher:
    def __init__(self):
        self._methods = {}
        for item in dir(self):
            item = getattr(self, item)
            if callable(item) and hasattr(item, "_dispatch_category"):
                method = getattr(item, "_dispatch_method")
                if method not in self._methods:
                    self._methods[method] = {}
                self._methods[method][item._dispatch_category] = item

    def dispatch(self, category, method="_", *args, **kwargs):
        return self._methods[method][category](*args, **kwargs)

    @staticmethod
    def on(category, method="_"):
        def wrapper(func):
            setattr(func, "_dispatch_category", category)
            setattr(func, "_dispatch_method", method)
            return func
        return wrapper
