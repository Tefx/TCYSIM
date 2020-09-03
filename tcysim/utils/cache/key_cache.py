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


class KeyCacheMethod:
    # Note: if the cached result will be set or dict, ensuring that: their hashes do not base on their memory locations,
    # or the ordering does not matter.
    def __init__(self, func):
        self.func = func
        self.store = {}
        self.current_instance = None
        self.current_ins_id = 0

    def __get__(self, instance, owner):
        ins_id = id(instance)
        if ins_id not in self.store:
            self.store[ins_id] = {}
        self.current_instance = instance
        self.current_ins_id = ins_id
        return self

    def __call__(self, *args):
        store = self.store[self.current_ins_id]
        if args not in store:
            store[args] = self.func(self.current_instance, *args)
        return store[args]

    def clear(self, obj, *args):
        assert (obj is self.current_instance)
        store = self.store[self.current_ins_id]
        if args in store:
            del store[args]


key_cache = KeyCacheMethod
