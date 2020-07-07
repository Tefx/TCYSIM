from ..interval_tree cimport IntervalTree, Interval


cdef class LoadPredicator:
    cdef dict arr_pools
    cdef dict dep_pools
    cdef IntervalTree itv_tree

    cdef double _cal_result
    cdef double _cal_start
    cdef double _cal_end
    cdef double _cal_cycle

    def __init__(self, double min_interval=0):
        self.arr_pools = {}
        self.dep_pools = {}
        self.itv_tree = IntervalTree(min_interval)

        self._cal_result = 1
        self._cal_start = -1
        self._cal_end = -1
        self._cal_cycle = 0

    def register_store(self, box, tuple arrival_interval):
        cdef double start, end
        start, end = arrival_interval
        self.arr_pools[box.id] = self.itv_tree.insert(start, end)

    def register_retrieve(self, box, tuple departure_interval):
        cdef double start, end
        start, end = departure_interval
        self.dep_pools[box.id] = self.itv_tree.insert(start, end)

    def unregister_store(self, box):
        box_id = box.id
        cdef Interval interval = self.arr_pools[box_id]
        interval.remove_from_tree()
        del self.arr_pools[box_id]

    def unregister_retrieve(self, box):
        cdef bytes box_id = box.id
        cdef Interval interval = self.dep_pools[box_id]
        interval.remove_from_tree()
        del self.dep_pools[box_id]

    def arrival_interval(self, box):
        return self.arr_pools[box.id]

    def departure_interval(self, box):
        return self.dep_pools[box.id]

    def probability_of_conflict(self, double start, double end, double min_cycle_time=180):
        self._cal_result = 1
        self._cal_start = start
        self._cal_end = end
        self._cal_cycle = min_cycle_time
        self.itv_tree.process_overlapped(start - min_cycle_time, end + min_cycle_time, self._calculator)
        return 1 - self._cal_result

    def _calculator(self, double a0, double a1):
        cdef double b0 = self._cal_start
        cdef double b1 = self._cal_end
        cdef double c = self._cal_cycle
        cdef double area = 0
        cdef double k, prob

        k = a1 - b1 + c
        if k > 0: area += k * k
        k = b0 - a0 + c
        if k > 0: area += k * k
        k = a0 - b1 + c
        if k > 0: area -= k * k
        k = a1 - b1 - c
        if k > 0: area -= k * k
        k = b0 - a1 + c
        if k > 0: area -= k * k
        k = b0 - a0 - c
        if k > 0: area -= k * k

        prob = 2 * c / (b1 - b0) - area / (2 * (a1 - a0) * (b1 - b0))
        self._cal_result *= (1 - prob)
