def print_on_start(self, op):
    equipment = op.equipment
    print("[{:.2f}]<Operation/Equipment {}.{}>[START]".format(
        self.time, str(id(equipment.blocks[0]))[-4:], equipment.idx),
        op, equipment.current_coord())


def print_on_finish_or_fail(self, op):
    equipment = op.equipment
    print("[{:.2f}]<Operation/Equipment {}.{}>[FINISH/FAIL]".format(
        self.time, str(id(equipment.blocks[0]))[-4:], equipment.idx),
        op, equipment.current_coord())
