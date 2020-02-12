from collections import deque


class ResuedIndexObject:
    __avail_idx = deque()
    __max_idx = 0

    __slots__ = ["__id"]

    def __init__(self):
        if self.__class__.__avail_idx:
            self.__id = self.__class__.__avail_idx.pop()
        else:
            self.__id = self.__class__.__max_idx
            self.__class__.__max_idx += 1

    def release(self):
        self.__class__.__avail_idx.append(self.__id)
        self.__id = -1

    def __del__(self):
        if self.__id >= 0:
            self.__class__.__avail_idx.append(self.__id)

    def __hash__(self):
        return self.__id

    def __eq__(self, other):
        return self.__id == other.__id


class IncreaseIndexObject:
    __slots__ = ["__id"]

    __max_idx = 0

    def __init__(self):
        self.__id = self.__class__.__max_idx
        self.__class__.__max_idx += 1

    def __hash__(self):
        return self.__id

    def __eq__(self, other):
        return self.__id == other.__id

IndexObject = IncreaseIndexObject