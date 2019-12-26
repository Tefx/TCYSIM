from collections import deque
from math import sqrt

from .motion import Motion


class Spec:
    def __init__(self, v, a, d=None):
        self.v = v
        self.a = a
        if d is None:
            self.d = a
        else:
            self.d = d

        self._cache_w0 = self.v ** 2 * (self.a + self.d) / 2 / self.a / self.d
        self._cache_w1 = 2 * self.a * self.d / (self.a + self.d)


class Mover:
    def __init__(self, specs):
        self.curr_v = 0
        self.curr_a = 0
        self._state_curr_v = None
        self._state_curr_a = None
        self.pending_motions = deque()
        self.loc = None
        self.time = -1

        if isinstance(specs, dict):
            self.specs = specs
        else:
            self.specs = {"default": specs}

        # self._cache_w0 = self.spec_v ** 2 * (a + d) / 2 / a / d
        # self._cache_w1 = 2 * self.spec_a * self.spec_d / (self.spec_a + self.spec_d)

    def save_state(self):
        self._state_curr_v = self.curr_v
        self._state_curr_a = self.curr_a

    def restore_state(self):
        self.curr_v = self._state_curr_v
        self.curr_a = self._state_curr_a

    def perform_motion(self, m):
        self.loc += m.displacement
        self.time = m.finish_time
        self.curr_v = m.finish_velocity
        self.curr_a = m.a

    def sync_with(self, other):
        self.loc = other.loc
        self.time = other.time
        self.curr_v = other.curr_v
        self.curr_a = other.curr_a

    def run_until(self, time):
        while self.pending_motions and self.pending_motions[0].start_time < time:
            m = self.pending_motions[0]
            if m.finish_time <= time:
                m = self.pending_motions.popleft()
            else:
                m = m.split(time)
            self.perform_motion(m)
        return len(self.pending_motions)

    def interrupt(self):
        if not self.idle() and self.allow_interruption:
            self.pending_motions.clear()

    def idle(self):
        return not self.pending_motions

    def allow_interruption(self):
        return self.idle() or self.pending_motions[0].allow_interruption

    def available_time(self, interrupt=False):
        time = 0
        for m in self.pending_motions:
            if interrupt and m.interruptable:
                break
            time += m.timespan
        return time

    def create_motions(self, start_time, displacement, allow_interruption=False, spec="default"):
        spec = self.specs[spec]
        v0 = self.curr_v
        a = spec.a
        d = spec.d
        vm = spec.v
        w0 = spec._cache_w0
        w1 = spec._cache_w1
        st = start_time

        # print(v0, a, displacement, v0 * v0 / 2 / d)
        motions = []
        if v0 > 0 and displacement < v0 * v0 / 2 / d:
            t0 = v0 / d
            s0 = v0 * t0 - 0.5 * d * t0 * t0
            motions.append(Motion(st, t0, v0, -d, allow_interruption=allow_interruption))
            displacement -= s0
            v0 = 0
            st += t0
        elif v0 < 0 and displacement > -v0 * v0 / 2 / d:
            t0 = -v0 / d
            s0 = -v0 * t0 + 0.5 * d * t0 * t0
            motions.append(Motion(st, t0, v0, d, allow_interruption=allow_interruption))
            displacement += s0
            v0 = 0
            st += t0

        v0 = abs(v0)
        distance = abs(displacement)
        dflg = 1 if displacement >= 0 else -1

        # print(v0, distance, dflg, w0 - v0 * v0 / 2 / a, motions)

        if distance >= w0 - v0 * v0 / 2 / a:
            t0 = (vm - v0) / a
            t1 = distance / vm - vm / w1 + v0 * v0 / 2 / a / vm
            t2 = vm / d
            # if self.curr_v < 0:
            #     v0 = -v0
            #     vm = -vm
            #     a = -a
            #     d = -d
            # print("#", t0, t1, v0, a, dflg, v0 * dflg, a * dflg)
            if t0 > 0:
                motions.append(Motion(st, t0, v0 * dflg, a * dflg, allow_interruption=allow_interruption))
                st += t0
            if t1 > 0:
                motions.append(Motion(st, t1, vm * dflg, 0, allow_interruption=allow_interruption))
                st += t1
            if t2 > 0:
                motions.append(Motion(st, t2, vm * dflg, -d * dflg, allow_interruption=allow_interruption))
                st += t2
        elif distance >= v0 * v0 / 2 / d:
            vx = sqrt(w1 * (distance + v0 * v0 / 2 / a))
            t0 = (vx - v0) / a
            t1 = vx / d
            # if self.curr_v < 0:
            #     v0 = -v0
            #     vx = -vx
            #     a = -a
            #     d = -d
            if t0 > 0:
                motions.append(Motion(st, t0, v0 * dflg, a * dflg, allow_interruption=allow_interruption))
                st += t0
            if t1 > 0:
                motions.append(Motion(st, t1, vx * dflg, -d * dflg, allow_interruption=allow_interruption))
                st += t1

        # if self.axis == 2:
        #     print(start_time, displacement, self.curr_v, self.curr_a, motions, dflg)

        if motions:
            self.curr_v = motions[-1].finish_velocity
            self.curr_a = motions[-1].a
        return st - start_time, motions

    def commit_motions(self, motions):
        self.pending_motions.extend(motions)
