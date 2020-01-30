from collections import deque
from libc.math cimport sqrt, fabs

from .motion cimport Motion

cdef class Spec:
    def __cinit__(self, double v, double a, double d=-1):
        self.v = v
        self.a = a
        if d < 0:
            d = a
        self.d = d

        self._cache_w0 = v * v * (a + d) / (2 * a * d)
        self._cache_w1 = 2 * a * d / (a + d)

cdef class Mover:
    def __init__(self, specs):
        self.curr_v = 0
        self.curr_a = 0
        self._state_curr_v = 0
        self._state_curr_a = 0
        self.pending_motions = deque()
        self.loc = 0
        self.time = -1

        if isinstance(specs, dict):
            self.specs = specs
        else:
            self.specs = {"default": specs}

    def save_state(self):
        self._state_curr_v = self.curr_v
        self._state_curr_a = self.curr_a

    def restore_state(self):
        self.curr_v = self._state_curr_v
        self.curr_a = self._state_curr_a

    cdef void perform_motion(self, Motion m):
        self.loc += m.displacement
        self.time = m.finish_time
        self.curr_v = m.finish_velocity
        self.curr_a = m.a

    def sync_with(self, Mover other):
        self.loc = other.loc
        self.time = other.time
        self.curr_v = other.curr_v
        self.curr_a = other.curr_a

    def run_until(self, double time):
        cdef Motion m
        while self.pending_motions:
            m = self.pending_motions[0]
            if m.start_time >= time:
                break
            if m.finish_time <= time:
                m = self.pending_motions.popleft()
            else:
                m = m.split(time)
            self.perform_motion(m)
        return len(self.pending_motions)

    def interrupt(self):
        if not self.idle() and self.allow_interruption():
            self.pending_motions.clear()

    cdef bint idle(self):
        return not self.pending_motions

    cpdef bint allow_interruption(self):
        cdef Motion m
        if self.idle():
            return True
        else:
            m = self.pending_motions[0]
            return m.allow_interruption

    def available_time(self, bint interrupt=False):
        cdef Motion m
        cdef double time = 0
        for m in self.pending_motions:
            if interrupt and m.allow_interruption:
                break
            time += m.timespan
        return time

    cdef tuple create_motions(self, double start_time, double displacement, bint allow_interruption=False, mode="default"):
        cdef Spec spec = self.specs[mode]
        cdef double v0 = self.curr_v
        cdef double a = spec.a
        cdef double d = spec.d
        cdef double vm = spec.v
        cdef double w0 = spec._cache_w0
        cdef double w1 = spec._cache_w1
        cdef double st = start_time
        cdef double t0, t1, t2, dflg, vx
        cdef Motion m

        motions = []
        if v0 > 0 and displacement < v0 * v0 / (2 * d):
            t0 = v0 / d
            s0 = v0 * t0 - 0.5 * d * t0 * t0
            m = Motion(st, t0, v0, -d, allow_interruption=allow_interruption)
            motions.append(m)
            displacement -= s0
            v0 = 0
            st += t0
        elif v0 < 0 and displacement > -v0 * v0 / (2 * d):
            t0 = -v0 / d
            s0 = -v0 * t0 + 0.5 * d * t0 * t0
            m = Motion(st, t0, v0, d, allow_interruption=allow_interruption)
            motions.append(m)
            displacement += s0
            v0 = 0
            st += t0

        v0 = fabs(v0)
        distance = fabs(displacement)
        dflg = 1 if displacement >= 0 else -1

        if distance >= w0 - v0 * v0 / (2 * a):
            t0 = (vm - v0) / a
            t1 = distance / vm - vm / w1 + v0 * v0 / (2 * a * vm)
            t2 = vm / d
            if t0 > 0:
                m = Motion(st, t0, v0 * dflg, a * dflg, allow_interruption=allow_interruption)
                motions.append(m)
                st += t0
            if t1 > 0:
                m = Motion(st, t1, vm * dflg, 0, allow_interruption=allow_interruption)
                motions.append(m)
                st += t1
            if t2 > 0:
                m = Motion(st, t2, vm * dflg, -d * dflg, allow_interruption=allow_interruption)
                motions.append(m)
                st += t2
        elif distance >= v0 * v0 / (2 * d):
            vx = sqrt(w1 * (distance + v0 * v0 / (2 * a)))
            t0 = (vx - v0) / a
            t1 = vx / d
            if t0 > 0:
                m = Motion(st, t0, v0 * dflg, a * dflg, allow_interruption=allow_interruption)
                motions.append(m)
                st += t0
            if t1 > 0:
                m = Motion(st, t1, vx * dflg, -d * dflg, allow_interruption=allow_interruption)
                motions.append(m)
                st += t1

        if motions:
            m = motions[len(motions) - 1]
            self.curr_v = m.finish_velocity
            self.curr_a = m.a

        return st - start_time, motions

    cpdef void commit_motions(self, motions):
        self.pending_motions.extend(motions)
