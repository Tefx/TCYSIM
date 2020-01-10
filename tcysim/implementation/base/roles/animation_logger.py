from pickle import dump

from pesim import TIME_FOREVER
from tcysim.framework.roles import Observer


class AnimationLogger(Observer):
    def __init__(self, yard, start=0, end=TIME_FOREVER, fps=60, speedup=1):
        super(AnimationLogger, self).__init__(yard=yard, start=start, end=end, interval=speedup / fps)
        self.log = []
        self.last_log = None
        self.box_last_positions = {}
        self.crane_last_position = {}

    def on_observe(self):
        equ_coords = {}
        box_coords = {}

        for i, equipment in enumerate(self.yard.equipments):
            # if equipment.state == equipment.STATE.WORKING or i not in self.crane_last_position:
            coord = equipment.current_coord(transform_to="g")
            if i not in self.crane_last_position or coord != self.crane_last_position[i]:
                self.crane_last_position[i] = coord
                equ_coords[i] = coord.to_tuple()

        current_box_location = {}
        for box in self.yard.boxes:
            # if box.state != box.STATE.STORED or box.id not in self.box_last_positions:
            coord = box.current_coord(transform_to="g")
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
