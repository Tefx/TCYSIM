from copy import copy
from random import shuffle

from pesim import Process
from ..equipment import Equipment
from ..priority import Priority
from ..request import ReqStatus
from .pool import ReqPool


class TaskScheduler(Process):
    def __init__(self, block):
        self.pool = ReqPool()
        self.block = block
        self.equipments = block.equipments
        self.skd_equipments = []
        self.skd_reason = None
        super(TaskScheduler, self).__init__(block.yard.env)

    def choose_task(self, time, equipment, tasks):
        for task in tasks:
            if task.is_ready():
                return task

    def choose_equipment(self, time, request, equipments):
        for equipment in equipments:
            return equipment

    def _process(self):
        self.on_schedule(self.time)
        self.skd_equipments = []
        self.skd_reason = False

    def schedule(self, time, equipment=None, reason=None):
        if equipment:
            self.skd_equipments.append(equipment)
        else:
            self.skd_equipments = copy(self.equipments)
        self.skd_reason = reason
        self.activate(time, Priority.SCHEDULE)

    def on_schedule(self, time):
        self.refresh_pool(time)

        equipments = list(filter(Equipment.ready_for_new_task, self.skd_equipments))
        shuffle(equipments)

        for equipment in equipments:
            avail_tasks = self.pool.available_requests(equipment)
            request = self.choose_task(time, equipment, avail_tasks)
            if request is not None:
                self.pool.pop(request)
                setattr(request, "time", time)
                equipment.submit_task(request)

    def refresh_pool(self, time):
        for request in self.pool.available_requests():
            if request.status >= ReqStatus.READY:
                equipment = self.equipment_for_request(time, request)
                if equipment:
                    self.pool.repush(request, equipment=equipment)

    def equipment_for_request(self, time, request):
        if not request.equipment:
            equipments = request.block.equipments
            request.equipment = self.choose_equipment(time, request, equipments)
        return request.equipment

    def submit_request(self, time, request):
        access_point = request.access_point
        equipment = self.equipment_for_request(time, request)
        self.pool.push(request, equipment, access_point)
        self.schedule(time, equipment=equipment)

