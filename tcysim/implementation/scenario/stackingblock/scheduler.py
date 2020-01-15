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
        task = min(filter(Request.is_ready, tasks), key=self.rank_task, default=None)
        return task

    def on_idle(self, time):
        eqp_coord = self.equipment.current_coord(transform_to="g")
        max_height = self.equipment.hoist.max_height
        if abs(eqp_coord.z - max_height) > 0.1:
            dst_loc = self.equipment.coord_g2l(eqp_coord.set1("z", max_height))
            return self.equipment.op_builder.MoveOp(dst_loc)