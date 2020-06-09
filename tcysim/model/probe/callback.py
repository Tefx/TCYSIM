def print_before(self, callback):
    print("Callback[before]:", self.time, id(callback), callback.func.__name__, callback.args, callback.kwargs)

def print_after(self, callback):
    print("Callback[after]:", self.time, id(callback), callback.func.__name__, callback.args, callback.kwargs)
