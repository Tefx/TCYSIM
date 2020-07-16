class KeyCache:
    def __init__(self, func):
        self.func = func
        self.store = {}

    def __getitem__(self, item):
        if item not in self.store:
            self.store[item] = self.func(item)
        return self.store[item]

    def get(self, item):
        if item not in self.store:
            self.store[item] = self.func(item)
        return self.store[item]

def key_cache(func):
    _cache = KeyCache(lambda args: func(*args))
    def wrapped(*args):
        return _cache.get(args)
    return wrapped
