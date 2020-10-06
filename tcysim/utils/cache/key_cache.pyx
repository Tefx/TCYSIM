from libc.stdint cimport uintptr_t

cdef class KeyCache:
    cdef object func
    cdef dict store

    def __init__(self, func):
        self.func = func
        self.store = {}

    def __getitem__(self, item):
        if item not in self.store:
            self.store[item] = self.func(item)
        return self.store[item]

    cpdef object get(self, item):
        if item not in self.store:
            self.store[item] = self.func(item)
        return self.store[item]


cdef class KeyCacheMethod:
    # Note: if the cached result will be set or dict, ensuring that: their hashes do not base on their memory locations,
    # or the ordering does not matter.

    cdef object func
    cdef dict store
    cdef object cur_ins

    def __init__(self, object func):
        self.func = func
        self.store = {}
        self.cur_ins = None

    def __get__(self, object instance, object owner):
        self.cur_ins = instance
        return self

    def __call__(self, *args):
        cdef dict store = self.store.get(self.cur_ins, None)
        cdef object res
        if store is None:
            store = {}
            self.store[self.cur_ins] = store
            res = None
        else:
            res = store.get(args, None)
        if res is None:
            res = self.func(self.cur_ins, *args)
            store[args] = res
        return res

    def clear(self, *args):
        store = self.store[self.cur_ins]
        if args in store:
            del store[args]

    def clear_all(self):
        self.store[self.cur_ins] = {}

cdef class PatchedKeyCacheMethod:
    # Note: if the cached result will be set or dict, ensuring that: their hashes do not base on their memory locations,
    # or the ordering does not matter.

    cdef object func
    cdef dict store
    cdef object obj

    def __init__(self, object func, object obj=None):
        self.func = func
        self.store = {}
        self.obj = obj

    def instantiate(self, object obj):
        return self.__class__(self.func, obj)

    def patch_init(self, init):
        def patched(obj, *args, **kwargs):
            for name, method in obj._kcm_fields:
                method = method.instantiate(obj)
                setattr(obj, name, method)
            init(obj, *args, **kwargs)
        return patched

    def __set_name__(self, owner, name):
        if not hasattr(owner, "_kcm_fields"):
            setattr(owner, "_kcm_fields", [])
            owner.__init__ = self.patch_init(owner.__init__)
        owner._kcm_fields.append((name, self))

    def __call__(self, *args):
        cdef object res = self.store.get(args, None)
        if res is None:
            res = self.func(self.obj, *args)
            self.store[args] = res
        return res

    def clear(self, *args):
        if args in self.store:
            del self.store[args]

    def clear_all(self):
        self.store = {}

key_cache = PatchedKeyCacheMethod
