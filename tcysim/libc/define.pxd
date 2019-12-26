from libc.stdint cimport int64_t, int32_t

DEF _BOX_ID_LEN_LIMIT=32
DEF _TIME_INF=31536000

BOX_ID_LEN_LIMIT = _BOX_ID_LEN_LIMIT
TIME_INF = _TIME_INF

cdef extern from "define.h":
    ctypedef int bool

    ctypedef enum BoxSize:
        BOX_SIZE_TWENTY
        BOX_SIZE_FORTY

    ctypedef enum BoxState:
        BOX_STATE_INITIAL = 0
        BOX_STATE_ALLOCATED = 1
        BOX_STATE_STORING = 2
        BOX_STATE_STORED = 3
        BOX_STATE_RESHUFFLING = 4
        BOX_STATE_RETRIEVING = 5
        BOX_STATE_RETRIEVED = 6

    ctypedef enum SlotUsage:
        SLOT_USAGE_FREE
        SLOT_USAGE_TWENTY_ONLY
        SLOT_USAGE_FORTY_ONLY
        SLOT_USAGE_FORTY_ONLY_END

    ctypedef int64_t Time
    ctypedef int32_t CellIdx
    ctypedef struct Block

    ctypedef struct Box:
        char id[_BOX_ID_LEN_LIMIT]
        BoxSize size
        BoxState state
        Time alloc_time, store_time, retrieval_time
        CellIdx loc[3]
        Block *block
        void* _self

    ctypedef Box *Cell

    ctypedef struct Block:
        CellIdx shape[3]
        bool column_sync[3]
        SlotUsage *column_use_type[3]
        CellIdx *column_usage[3]
        CellIdx *column_usage_occupied[3]
        CellIdx cell_num
        Cell *cells
        int stacking_axis
        int box_orientation
        bool *lock_map
        void* _self

cdef extern from "box.h":
    void box_init(Box *box, char *box_id, BoxSize size)
    void box_destroy(Box *box)
    int box_alloc(Box *box, Time time)
    int box_store(Box *box, Time time)
    int box_retrieve(Box *box, Time time)
    int box_reshuffle(Box *box, int32_t *new_loc)
    bool box_location_is_valid(Box* box, Block* blk, CellIdx * loc)

cdef extern from "block.h":
    void block_init(Block *blk, const CellIdx *shape, int box_orientation, int stacking_axis, const int *axis_need_sync)
    void block_destroy(Block *blk)
    int block_usage(Block *blk, const CellIdx *loc, bool include_occupied)
    Box* block_box_at(Block* blk, const CellIdx* idx)
    Box* block_top_box(Block* blk, const CellIdx* idx, int along)

    void block_lock(Block *blk, const CellIdx* idx)
    void block_unlock(Block *blk, const CellIdx* idx)
    bool block_is_locked(Block *blk, const CellIdx* idx)

cdef extern from "path.h":
    ctypedef struct PathFrameChunk
    ctypedef struct PathTrace:
        int chunk_size;
        PathFrameChunk* chunks
        PathFrameChunk* last_chunk
        float max, min;

    void pathtrace_init(PathTrace *pt, int chunk_size)
    void pathtrace_destroy(PathTrace *pt)
    void pathtrace_append_frame(PathTrace *pt, Time time, float coord, void *other)
    bool pathtrace_intersect_test_with_clearance(PathTrace *pt0, PathTrace *pt1, float clearance, float shift)
    float pathtrace_boundary(PathTrace* pt, float* pmax, float* pmin)

