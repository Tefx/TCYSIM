from multiprocessing import Process, Value, Array, Semaphore
from inspect import signature, Signature
import ctypes


class SharedBytes:
    __slots__ = ["array", "len"]

    def __init__(self, *args, **kwargs):
        self.array = Array(ctypes.c_char, *args, **kwargs)
        self.len = Value(ctypes.c_int64, lock=False)

    @property
    def value(self):
        return self.array.raw[:self.len.value]

    @value.setter
    def value(self, v):
        self.len.value = len(v)
        self.array.raw = v


class Method_LMP:
    __slots__ = ["idx", "func", "ins", "wait_value", "wait_sem", "idle_sem",
                 "params", "ret", "ret_sem", "last_received", "ret_is_tuple"]

    def __init__(self, idx, func, ins, wait_value, wait_sem, idle_sem):
        self.idx = idx
        self.func = func
        self.ins = ins
        self.wait_value = wait_value
        self.wait_sem = wait_sem
        self.idle_sem = idle_sem

        self.params = None
        self.ret = None
        self.ret_sem = None
        self.last_received = True

        self.build()


    @classmethod
    def create_shared_value_by_pytype(cls, a):
        if a is int:
            return Value(ctypes.c_int64, lock=False)
        elif a is float:
            return Value(ctypes.c_double, lock=False)
        elif a is bytes:
            return Array(ctypes.c_char, 1024, lock=False)
        elif a is str:
            return Array(ctypes.c_wchar, 1024, lock=False)
        elif isinstance(a, str):
            if a.startswith("str"):
                return Array(ctypes.c_wchar, int(a[4:-1]), lock=False)
            elif a.startswith("bytes"):
                return Array(ctypes.c_char, int(a[6:-1]), lock=False)
            elif a.startswith("raw"):
                return SharedBytes(int(a[4:-1]), lock=False)
        elif isinstance(a, tuple):
            return tuple(cls.create_shared_value_by_pytype(x) for x in a)
        elif a is None or a is Signature.empty:
            return None
        raise NotImplementedError("Unknown type: {}".format(a))

    def build(self):
        self.params = []
        sig = signature(self.func)
        for name, p in sig.parameters.items():
            if name not in ("self", "cls"):
                self.params.append(self.create_shared_value_by_pytype(p.annotation))
        self.ret = self.create_shared_value_by_pytype(sig.return_annotation)
        self.ret_is_tuple = isinstance(self.ret, tuple)
        self.ret_sem = Semaphore(0)
        self.last_received = True

    def __call__(self, *args):
        if not self.last_received:
            self.ret_sem.acquire()
        else:
            self.last_received = False
        self.idle_sem.acquire()
        for p, a in zip(self.params, args):
            p.value = a
        self.wait_value.value = self.idx
        self.wait_sem.release()
        return self

    def get_result(self):
        self.ret_sem.acquire()
        self.last_received = True
        if self.ret is not None:
            if self.ret_is_tuple:
                return tuple(v.value for v in self.ret)
            else:
                return self.ret.value

    def invoke(self):
        res = self.func(*(v.value for v in self.params))
        if res is not None:
            if self.ret_is_tuple:
                for r, x in zip(self.ret, res):
                    r.value = x
            else:
                self.ret.value = res
        self.idle_sem.release()
        self.ret_sem.release()


class SingleLMP(Process):
    remote_names = []

    def __init__(self):
        super(SingleLMP, self).__init__()
        self.wait_value = Value(ctypes.c_int8, lock=False)
        self.wait_sem = Semaphore(0)
        self.idle_sem = Semaphore(1)

        self.libs = []
        _exclude_names = dir(Process)
        for name in dir(self):
            if name in _exclude_names:
                continue
            item = getattr(self, name)
            if name in self.remote_names or getattr(item, "is_remote", False):
                m = Method_LMP(len(self.libs), item, self, self.wait_value, self.wait_sem, self.idle_sem)
                self.libs.append(m)
                self.__dict__["{}_r".format(item.__name__)] = m

    @staticmethod
    def remote(func):
        func.is_remote = True
        return func

    def finish(self):
        self.wait_value.value = -1
        self.wait_sem.release()
        self.join()

    def run(self) -> None:
        try:
            while True:
                self.wait_sem.acquire()
                idx = self.wait_value.value
                if idx < 0:
                    break
                self.libs[idx].invoke()
        except KeyboardInterrupt:
            pass
