from pesim import TIME_FOREVER
from tcysim.utils import V3, RotateOperator
from tcysim.framework.layout import LayoutItem
import pickle
import msgpack

from .file import FileTree
from .compress import CompressDict

class TraceReader(FileTree):
    def __init__(self, path):
        super(TraceReader, self).__init__(path)
        self.box_dwell = {}
        self._cd = CompressDict(self.get_file_r("dict"))
        self.basic_info = self.load_basic_info()

    def load(self, file):
        yield from msgpack.Unpacker(file, strict_map_key=False, use_list=False)

    def load_basic_info(self):
        return next(self.load(self.get_file_r("info")))[0]

    def load_box_dwell(self, block_id):
        if block_id not in self.box_dwell:
            self.box_dwell[block_id] = {}
            file = self.get_file_r("block", block_id, "box_dwell")
            if file:
                for box_id, time, flag in self.load(file):
                    box_id = self._cd.decompress(box_id)
                    if box_id not in self.box_dwell[block_id]:
                        self.box_dwell[block_id][box_id] = [0, TIME_FOREVER, flag]
                    if flag > 0:
                        self.box_dwell[block_id][box_id][0] = time
                        self.box_dwell[block_id][box_id][2] = flag
                    else:
                        self.box_dwell[block_id][box_id][1] = time
        return self.box_dwell[block_id]

    def boxes_within(self, block_ids, start_time=0, end_time=TIME_FOREVER):
        box_set = {}
        for block_id in block_ids:
            rotate = self.basic_info["Block"][block_id]["Rotate"]
            for box_id, item in self.load_box_dwell(block_id).items():
                if box_id in box_set:
                    if item[2] == 0:
                        box_set[box_id][1] = item[1]
                    else:
                        item[1] = box_set[box_id][1]
                        box_set[box_id] = item + [rotate]
                else:
                    box_set[box_id] = item + [rotate]
        return {box_id: [size, rotate, 1, -1, -1, -1, -1, arrival_time, departure_time]
                for box_id, (arrival_time, departure_time, size, rotate)
                in box_set.items()
                if arrival_time < end_time and
                departure_time > start_time}

    def find_box_intervals_by_equipment(self, equipment_name, start_time, end_time, box_set=None):
        file = self.get_file_r("equipment", equipment_name, "box_moves")
        equipment_info = self.basic_info["Equipment"][equipment_name]
        fake_layout_item = LayoutItem(V3(*equipment_info["Offset"]), V3.zero(), equipment_info["Rotate"])
        latest_time_before = -1
        boxes = {}
        latest_pos_before = {}
        res = []
        for box_id, flag, time, *other in self.load(file):
            box_id = self._cd.decompress(box_id)
            if box_set and box_id not in box_set:
                continue
            if flag:
                if time < end_time:
                    start_pos = fake_layout_item.transform_to(V3(*other), "g").to_tuple()
                    boxes[box_id] = [min(time, end_time), end_time, start_pos, None]
            else:
                if latest_time_before < time < start_time:
                    latest_time_before = time
                    latest_pos_before[box_id] = latest_time_before, fake_layout_item.transform_to(V3(*other), "g").to_tuple()
                    del boxes[box_id]
                elif box_id in boxes:
                    if boxes[box_id][0] >= end_time:
                        del boxes[box_id]
                    else:
                        if time < end_time:
                            boxes[box_id][1] = time
                            boxes[box_id][3] = fake_layout_item.transform_to(V3(*other), "g").to_tuple()
                        else:
                            boxes[box_id][1] = end_time
                        res.append((*boxes[box_id], box_id))
                        del boxes[box_id]
        for box_id, (start_time, end_time, start_pos, end_pos) in boxes.items():
            res.append((start_time, end_time, start_pos, end_pos, box_id))
        return latest_pos_before, res

    def load_motions(self, equipment_name, start_time=0, end_time=TIME_FOREVER):
        file = self.get_file_r("equipment", equipment_name, "motions")
        return tuple(record for record in self.load(file) if record[0] < end_time and record[0] > start_time - 1200)

    def build_moves(self, ts, base_time, pos, moves, last_v, last_t):
        if base_time > last_t:
            ts.append([base_time, last_v, 0, pos])
            last_t = base_time
        elif base_time < last_t:
            i = -1
            while ts[i][0] > base_time:
                i -= 1
            del ts[i+1:]
            dt = base_time - ts[-1][0]
            last_v = ts[-1][1] + ts[-1][2] * dt
            last_t = base_time
            ts.append([base_time, last_v, 0, pos])
        else:
            ts[-1][3] = pos

        if moves is None:
            return last_v, last_t

        loc = 0
        while loc < len(moves):
            t = moves[loc] + base_time
            v = moves[loc + 1]
            dt = t - last_t
            pos += last_v * dt
            last_v = v
            if t != last_t:
                ts.append([t, last_v, 0, pos])
                last_t = t
            else:
                ts[-1][1] = last_v

            n_moves = moves[loc + 2]
            loc += 3
            for i in range(n_moves):
                a = moves[loc]
                dt = moves[loc + 1]
                ts[-1][2] = a
                pos += last_v * dt + a * dt * dt / 2
                if pos < -10000:
                    exit()
                last_v += a * dt
                last_t += dt
                ts.append([last_t, last_v, 0, pos])
                loc += 2
        return last_v, last_t

    def rebuild_motions(self, equipment_name, motions):
        last_t = [0, 0, 0]
        last_v = [0, 0, 0]
        ts = [[], [], []]
        for base_time, pos, moves in motions:
            for axis in range(3):
                last_v[axis], last_t[axis] = self.build_moves(ts[axis], base_time, pos[axis],
                                                              moves[axis] if axis in moves else None,
                                                              last_v[axis], last_t[axis])
        for i in range(3):
            if not ts[i]:
                ts[i].append([TIME_FOREVER, 0, 0, 0])
            ts[i].append([TIME_FOREVER, 0, 0, ts[i][-1][3]])
        return ts

    def interpolate(self, ts, start_time, end_time, interval=1):
        cp = [0, 0, 0]
        first_times = tuple(ts[i][0][0] for i in range(3))
        min_time = min(first_times)
        min_time -= min_time % interval
        time = min(max(start_time, min_time), end_time)
        while True:
            liner_flag = True
            pos = []
            for i in range(3):
                if time < first_times[i]:
                    pos.append(ts[i][0][3])
                else:
                    while ts[i][cp[i] + 1][0] <= time: cp[i] += 1
                    t, v, a, p = ts[i][cp[i]]
                    dt = time - t
                    liner_flag = liner_flag and a == 0
                    pos.append(p + v * dt + a * dt * dt / 2)
            yield time, *pos
            if time >= end_time:
                break
            elif liner_flag:
                next_time = min(ts[i][cp[i] + 1][0] for i in range(3))
                next_time -= next_time % interval
                time = max(time + interval, min(end_time, next_time))
            else:
                time += interval

    def build_trajectory(self, equipment_name, start_time, end_time, interval=1, to_global=True):
        import numpy as np
        motions = self.load_motions(equipment_name, start_time, end_time)
        equipment_info = self.basic_info["Equipment"][equipment_name]

        if not motions:
            if to_global:
                return [[start_time, *equipment_info["Offset"]]]
            else:
                return [[[start_time, 0, 0, 0]] for _ in range(3)]

        ts = self.rebuild_motions(equipment_name, motions)

        if to_global:
            arr = np.array(list(self.interpolate(ts, start_time, end_time, interval)))
            rtt = RotateOperator(equipment_info["Rotate"])
            offset = equipment_info["Offset"]
            x = arr[:, 1] * rtt.cosv - arr[:, 2] * rtt.sinv + offset[0]
            y = arr[:, 1] * rtt.sinv + arr[:, 2] * rtt.cosv + offset[1]
            arr[:, 1] = x
            arr[:, 2] = y
            arr[:, 3] += offset[2]
            return arr.tolist()
        else:
            for i in range(3):
                if ts[i][0][0] > start_time:
                    ts[i] = [[start_time, 0, 0, ts[i][0][3]]] + ts[i]
            return ts

    def build_script(self, block_ids, start_time=0, end_time=TIME_FOREVER, speedup=10, fps=24, to_global=True):
        if block_ids is None:
            block_ids = list(self.basic_info["Block"].keys())
        interval = speedup / fps
        equipment_names = set()
        block_info = {}
        box_set = self.boxes_within(block_ids, start_time, end_time)
        for block_id in block_ids:
            b_info = self.basic_info["Block"][block_id]
            equipment_names.update(b_info["Equipments"])
            block_info[block_id] = dict(
                Offset=b_info["Center"],
                Scale=b_info["Scale"],
                Rotate=b_info["Rotate"],
            )
        equipment_script = {}
        box_initial_pos = {}
        moved_boxes = set()
        for equipment_name in equipment_names:
            e_info = self.basic_info["Equipment"][equipment_name]
            trajectory = self.build_trajectory(equipment_name, start_time, end_time, interval, to_global)
            box_pos, box_intervals = self.find_box_intervals_by_equipment(equipment_name, start_time, end_time, box_set)
            box_intervals.sort()
            moved_boxes.update(b[-1] for b in box_intervals)

            equipment_script[equipment_name] = dict(
                Offset=e_info["Offset"],
                Rotate=e_info["Rotate"],
                BoxRotate=e_info["BoxRotate"],
                BEDelta=e_info["BEDelta"],
                Trajectory=trajectory,
                BoxIntervals=box_intervals,
                PlotInfo=e_info["PlotInfo"]
            )

            for box_id, (time, pos) in box_pos.items():
                if box_id not in box_initial_pos or box_initial_pos[box_id][0] < time:
                    box_initial_pos[box_id] = (time, *pos)
                    box_set[box_id][3:7] = time, *pos

        for box_name in moved_boxes:
            box_set[box_name][2] = 0

        return dict(
            Info=dict(SpeedUp=speedup, FPS=fps, Start=start_time, End=end_time),
            BlockInfo=block_info,
            BoxInfo=box_set,
            BoxInitPos=box_initial_pos,
            EquipmentScript=equipment_script
        )

    def gather_box_info(self, box_set, all_box_intervals):
        box_info = {}
        for box_id, (size, rotate, fixed, last_time, first_pos_x, first_pos_y, first_pos_z, arrival_time, departure_time) in box_set.items():
            box_info[box_id] = (fixed, size, rotate, last_time, first_pos_x, first_pos_y, first_pos_z, arrival_time, departure_time, [])
        for equ, box_intervals in all_box_intervals:
            for start_time, end_time, start_pos, end_pos, box_id in box_intervals:
                box_info[box_id][-1].append((start_time, end_time, equ, start_pos, end_pos))
        for info in box_info.values():
            info[-1].sort()
        return box_info

    def build_script2(self, block_ids, start_time=0, end_time=TIME_FOREVER, speedup=10, fps=24, to_global=True):
        if block_ids is None:
            block_ids = list(self.basic_info["Block"].keys())
        interval = speedup / fps
        equipment_names = set()
        block_info = {}
        box_set = self.boxes_within(block_ids, start_time, end_time)
        for block_id in block_ids:
            b_info = self.basic_info["Block"][block_id]
            equipment_names.update(b_info["Equipments"])
            block_info[block_id] = dict(
                Offset=b_info["Center"],
                Scale=b_info["Scale"],
                Rotate=b_info["Rotate"],
                )
        equipment_script = {}
        # box_initial_pos = {}
        moved_boxes = set()
        all_box_intervals = []
        for equipment_name in equipment_names:
            e_info = self.basic_info["Equipment"][equipment_name]
            trajectory = self.build_trajectory(equipment_name, start_time, end_time, interval, to_global)
            box_pos, box_intervals = self.find_box_intervals_by_equipment(equipment_name, start_time, end_time, box_set)
            # box_intervals.sort()
            all_box_intervals.append((equipment_name, box_intervals))
            moved_boxes.update(b[-1] for b in box_intervals)

            equipment_script[equipment_name] = dict(
                Offset=e_info["Offset"],
                Rotate=e_info["Rotate"],
                BoxRotate=e_info["BoxRotate"],
                BEDelta=e_info["BEDelta"],
                Trajectory=trajectory,
                # BoxIntervals=box_intervals,
                PlotInfo=e_info["PlotInfo"]
                )

            for box_id, (time, pos) in box_pos.items():
                # if box_id not in box_initial_pos or box_initial_pos[box_id][0] < time:
                #     box_initial_pos[box_id] = (time, *pos)
                if box_set[box_id][3] < time:
                    box_set[box_id][3:7] = time, *pos

        for box_name in moved_boxes:
            box_set[box_name][2] = 0

        return dict(
            Info=dict(SpeedUp=speedup, FPS=fps, Start=start_time, End=end_time),
            BlockInfo=block_info,
            BoxInfo=self.gather_box_info(box_set, all_box_intervals),
            EquipmentScript=equipment_script
            )

    def dump_script(self, path, script):
        with open(path, "wb") as f:
            pickle.dump(script, f)

    def dump_as_json(self, path, script):
        import json
        with open(path, "w") as f:
            json.dump(script, f)
