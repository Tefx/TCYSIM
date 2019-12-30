from pickle import dump

from tcysim.framework.roles.observer import Observer


class PositionTracer(Observer):
    def __init__(self, *args, **kwargs):
        super(PositionTracer, self).__init__(*args, **kwargs)
        self.log = []
        self.last_log = None
        self.box_last_positions = {}
        self.crane_last_position = {}

    def on_observe(self):
        equ_coords = {}
        box_coords = {}

        for i, (equipment, coord) in enumerate(self.yard.equipment_coords()):
            if i not in self.crane_last_position or coord != self.crane_last_position[i]:
                self.crane_last_position[i] = coord
                equ_coords[i] = coord.to_tuple()

        current_box_location = {}
        for box in self.yard.boxes:
            coord = box.coord()
            if coord:
                current_box_location[box.id] = coord
                if box.id not in self.box_last_positions or self.box_last_positions[box.id] != coord:
                    box_coords[box.id] = box.teu, coord.to_tuple()
        self.box_last_positions = current_box_location

        if equ_coords or box_coords:
            self.log.append((self.time, equ_coords, box_coords))

    def __iter__(self):
        for item in self.log:
            yield item

    def dump(self, path):
        with open(path, "wb") as f:
            dump(self.log, f)