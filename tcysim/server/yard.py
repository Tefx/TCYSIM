class YardManager:
    def vessel_on_update(self):
        raise NotImplementedError

    def vessel_on_schedule(self):
        raise NotImplementedError

    def vessel_on_berth(self):
        raise NotImplementedError

    def box_query(self, box_id):
        raise NotImplementedError

    def box_alloc(self, time, box_id, x, y):
        raise NotImplementedError

    def box_notify_store(self, time, box_id):
        raise NotImplementedError

    def box_notify_retrieve(self, time, box_id):
        raise NotImplementedError

    def box_store(self, time, box_id):
        raise NotImplementedError

    def box_retrieve(self, time, box_id):
        raise NotImplementedError

    def handler_query_state(self, handler):
        raise NotImplementedError