import msgpack

from .file import FileTree
from .compress import CompressDict
from ..operation import OperationBase


class TraceWriter(FileTree):
    def __init__(self, yard, path):
        super(TraceWriter, self).__init__(path, erase=True)
        self.packer = None
        self._cd = CompressDict(self.get_file_w("dict"))
        self.dump_basic_info(yard)

    def dump(self, file, *obj):
        if self.packer is None:
            self.packer = msgpack.Packer()
        bytes = self.packer.pack(obj)
        file.write(bytes)

    def dump_basic_info(self, yard):
        collection = dict(
            Block={},
            Equipment={},
        )
        for block in yard.blocks.values():
            collection["Block"][block.id] = dict(
                Equipments=tuple(e.instance_name() for e in block.equipments),
                Center=block.center_coord("g").to_tuple(),
                Scale=(block.size / 2).to_tuple(),
                Rotate=(block.rotate),
            )

        for equipment in yard.equipments:
            collection["Equipment"][equipment.instance_name()] = dict(
                Offset=equipment.offset.to_tuple(),
                Rotate=equipment.rotate,
                BEDelta=equipment.BoxEquipmentDelta.to_tuple(),
                PlotInfo=equipment.plot_info(),
            )

        self.dump(self.get_file_w("info"), collection)

    def mark_arrival(self, box, time):
        self.dump(self.get_file_w("block", box.block.id, "box_dwell"),
                  self._cd.compress(box.id), time, box.size)

    def mark_departure(self, box, time):
        self.dump(self.get_file_w("block", box.block.id, "box_dwell"),
                  self._cd.compress(box.id), time, 0)

    def probe_on_op_finishing(self, op):
        if isinstance(op, OperationBase):
            equipment_name = op.equipment.instance_name()
            if op.box:
                f = self.get_file_w("equipment", equipment_name, "box_moves")
                if op.attach_time >= 0:
                    self.dump(f, self._cd.compress(op.box.id), True, op.attach_time, *op.attach_pos.to_tuple())
                if op.detach_time >= 0:
                    self.dump(f, self._cd.compress(op.box.id), False, op.detach_time, *op.detach_pos.to_tuple())
            rec = op.dump()
            if rec:
                self.dump(self.get_file_w("equipment", equipment_name, "motions"),
                          *rec)
