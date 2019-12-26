class Dispatcher:
    def __init__(self):
        self.methods = {}
        for item in dir(self):
            item = getattr(self, item)
            if callable(item) and hasattr(item, "_dispatch_type"):
                self.methods[item._dispatch_type] = item

    def dispatch(self, category, *args, **kwargs):
        return self.methods[category](*args, **kwargs)

    @staticmethod
    def on(category):
        def wrapper(func):
            setattr(func, "_dispatch_type", category)
            return func
        return wrapper
