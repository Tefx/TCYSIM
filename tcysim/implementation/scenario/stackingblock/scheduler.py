from tcysim.framework import Request, ReqState, JobScheduler


class CooperativeTwinCraneJobScheduler(JobScheduler):
    def rank_task(self, request: Request):
        if request.req_type == request.TYPE.ADJUST:
            return 0, request.ready_time
        elif hasattr(request, "coop_flag"):
            return 1, request.ready_time
        elif request.state == ReqState.RESUME_READY:
            return 2, -request.ready_time
        else:
            return 3, request.ready_time

    def choose_task(self, time, tasks):
        return min(filter(Request.is_ready, tasks), key=self.rank_task, default=None)

    def on_idle(self, time):
        if abs(self.equipment.local_coord().z - self.equipment.hoist.max_height) > 0.1:
            dst_loc = self.equipment.local_coord().set1(2, self.equipment.hoist.max_height)
            return self.equipment.op_builder.MoveOp(dst_loc)