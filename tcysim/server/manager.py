from abc import ABC, abstractmethod


class YardManager(ABC):
    @abstractmethod
    def vessel_on_update(self):
        pass

    @abstractmethod
    def vessel_on_schedule(self):
        pass

    @abstractmethod
    def vessel_on_berth(self):
        pass

    @abstractmethod
    def box_query(self, box_id):
        pass

    @abstractmethod
    def box_alloc(self, time, box_id, x, y):
        pass

    @abstractmethod
    def box_notify_store(self, time, box_id):
        pass

    @abstractmethod
    def box_notify_retrieve(self, time, box_id):
        pass

    @abstractmethod
    def box_store(self, time, box_id):
        pass

    @abstractmethod
    def box_retrieve(self, time, box_id):
        pass

    @abstractmethod
    def handler_query_state(self, handler):
        pass
