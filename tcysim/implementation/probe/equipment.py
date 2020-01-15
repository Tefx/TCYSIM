def print_info_on_collision(self, equipment, next_op, other_equipment):
    other_loc = other_equipment.current_coord(transform_to=equipment)
    print(equipment.time, equipment.current_coord().x, other_loc.x)
    print(equipment.state, other_equipment.state, next_op, other_equipment.current_op)
