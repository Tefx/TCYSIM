from tcysim.framework import JobScheduler


class CooperativeTwinCraneJobScheduler(JobScheduler):
    def rank_task(self, request):
        if request.req_type == request.TYPE.ADJUST:
            return 0, request.ready_time
        elif hasattr(request, "coop_flag"):
            return 1, request.ready_time
        elif request.state == request.STATE.RESUME_READY:
            return 2, -request.ready_time
        else:
            return 3, request.ready_time

    def on_idle(self, time):
        eqp_coord = self.equipment.current_coord(transform_to="g")
        max_height = self.equipment.hoist.max_height
        if abs(eqp_coord.z - max_height) > 0.1:
            dst_loc = self.equipment.coord_g2l(eqp_coord.set1("z", max_height))
            return self.equipment.op_builder.MoveOp(dst_loc)
