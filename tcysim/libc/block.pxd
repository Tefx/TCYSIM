from .define cimport *
from ..utils.vector cimport V3
from cpython cimport array
import array

cdef class CBlock:
    cdef Block_TCY c
    cpdef int count(self, int x= *, int y= *, int z= *, bint include_occupied= *)
    cpdef bint position_is_valid_for_size(self, int x, int y, int z, int teu)
    cpdef SlotUsage_TCY column_state(self, int x, int y, int z, int axis)
    cpdef object top_box(self, V3 loc, int along)

    cpdef array.array all_column_usage(self, int axis=?, bint include_occupied=?, array.array avail=?, array.array res=?)
    cpdef array.array all_slot_usage(self, int norm_axis, bint include_occupied=?, array.array avail=?, array.array res=?)
    cpdef array.array all_slot_states(self, int norm_axis, array.array res=?)
    cpdef array.array validate_all_slots(self, int norm_axis, int teu, array.array res=?)

    cpdef hook_before_alloc(self, box, V3 loc)
    cpdef hook_before_dealloc(self, box)
    cpdef hook_before_store(self, box)
    cpdef hook_before_retrieve(self, box)
