from libc.stdint cimport int64_t, int32_t

DEF _BOX_ID_LEN_LIMIT=32
DEF _TIME_INF=31536000

BOX_ID_LEN_LIMIT = _BOX_ID_LEN_LIMIT
TIME_INF = _TIME_INF

cdef extern from "define.h":
    ctypedef int bool

    ctypedef enum BoxSize_TCY:
        BOX_SIZE_TWENTY = 0
        BOX_SIZE_FORTY = 1

    ctypedef enum BoxState_TCY:
        BOX_STATE_INITIAL = 0
        BOX_STATE_ALLOCATED = 1
        BOX_STATE_STORING = 2
        BOX_STATE_STORED = 3
        BOX_STATE_RELOCATING = 4
        BOX_STATE_RETRIEVING = 5
        BOX_STATE_RETRIEVED = 6
        BOX_STATE_PLACEHOLDER = 7

    ctypedef enum SlotUsage_TCY:
        SLOT_USAGE_FREE = 0
        SLOT_USAGE_TWENTY_ONLY = 1
        SLOT_USAGE_FORTY_ONLY = 2
        SLOT_USAGE_FORTY_ONLY_END = 3

    ctypedef double Time_TCY
    ctypedef int32_t CellIdx_TCY
    ctypedef struct Block_TCY

    ctypedef struct Box_TCY:
        char id[_BOX_ID_LEN_LIMIT]
        BoxSize_TCY size
        BoxState_TCY state
        Time_TCY alloc_time, store_time, retrieval_time
        CellIdx_TCY loc[3]
        Block_TCY *block
        void*_self
        Box_TCY*_holder_or_origin

    ctypedef Box_TCY *Cell_TCY

    ctypedef struct Block_TCY:
        CellIdx_TCY spec[3]
        bool column_sync[3]
        SlotUsage_TCY *column_use_type[3]
        CellIdx_TCY *column_usage[3]
        CellIdx_TCY *column_usage_occupied[3]
        CellIdx_TCY cell_num
        Cell_TCY *cells
        int stacking_axis
        int box_orientation
        bool *lock_map
        void*_self

cdef extern from "box.h":
    void box_init(Box_TCY *box, char *box_id, BoxSize_TCY size)
    void box_destroy(Box_TCY *box)
    int box_alloc(Box_TCY *box, Time_TCY time)
    int box_store(Box_TCY *box, Time_TCY time)
    int box_retrieve(Box_TCY *box, Time_TCY time)
    # bool box_position_is_valid(Box *box, Block *blk, CellIdx *loc)
    void box_store_position(Box_TCY *box, CellIdx_TCY *id, bool new_locx)
    int box_place_holder(Box_TCY *box, CellIdx_TCY *new_loc)
    int box_remove_holder(Box_TCY *box)
    int box_realloc(Box_TCY *box, Time_TCY time, CellIdx_TCY *new_loc)
    void box_relocate_position(Box_TCY *box, CellIdx_TCY *loc)
    int box_relocate_alloc(Box_TCY *box, Time_TCY time, CellIdx_TCY *new_loc)
    int box_relocate_retrieve(Box_TCY *box, Time_TCY time)
    int box_relocate_store(Box_TCY *box, Time_TCY time)

cdef extern from "block.h":
    void block_init(Block_TCY *blk, const CellIdx_TCY *shape, int box_orientation, int stacking_axis,
                    const int *axis_need_sync)
    void block_destroy(Block_TCY *blk)
    int block_usage(Block_TCY *blk, const CellIdx_TCY *loc, bool include_occupied)
    Box_TCY*block_box_at(Block_TCY*blk, const CellIdx_TCY*idx)
    Box_TCY*block_top_box(Block_TCY*blk, const CellIdx_TCY*idx, int along)

    CellIdx_TCY blk_stack_hash(Block_TCY *blk, const CellIdx_TCY *idx)
    void block_lock(Block_TCY *blk, const CellIdx_TCY*idx)
    void block_unlock(Block_TCY *blk, const CellIdx_TCY*idx)
    bool block_is_locked(Block_TCY *blk, const CellIdx_TCY*idx)
    SlotUsage_TCY block_column_state(Block_TCY *blk, const CellIdx_TCY *idx, int axis)
    bool block_position_is_valid_for_size(Block_TCY *blk, CellIdx_TCY *loc, BoxSize_TCY box_size)
    int block_all_column_usages(Block_TCY *blk, int axis, bool include_occupied, const int *avail, int *results)
    int block_all_slot_usages(Block_TCY *blk, int norm_axis, bool include_occupied, const int *avail, int *results)
    int block_all_slot_states(Block_TCY *blk, int norm_axis, int*results)
    int block_validate_all_slots_for_size(Block_TCY *blk, int norm_axis, BoxSize_TCY box_size, bool *results)

cdef extern from "path.h":
    ctypedef struct PathFrameChunk
    ctypedef struct PathTrace:
        int chunk_size;
        PathFrameChunk*chunks
        PathFrameChunk*last_chunk
        double max, min;

    void pathtrace_init(PathTrace *pt, int chunk_size)
    void pathtrace_destroy(PathTrace *pt)
    void pathtrace_append_frame(PathTrace *pt, Time_TCY time, double pos, void *other)
    bool pathtrace_intersect_test_with_clearance(PathTrace *pt0, PathTrace *pt1, double clearance, double shift)
    double pathtrace_boundary(PathTrace*pt, double*pmax, double*pmin)
