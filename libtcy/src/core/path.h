//
// Created by tefx on 10/23/19.
//

#ifndef TCY_PATH_H
#define TCY_PATH_H

#include "define.h"

typedef struct {
    Time time;
    float coord;
    void* other;
} PathKeyFrame;

typedef struct PathFrameChunk{
    int num;
    PathKeyFrame* frames;
    struct PathFrameChunk* next;
} PathFrameChunk;

typedef struct{
    int chunk_size;
    PathFrameChunk* chunks;
    PathFrameChunk* last_chunk;
    float max, min;
} PathTrace;

DLLEXPORT void pathtrace_init(PathTrace *pt, int chunk_size);
DLLEXPORT void pathtrace_destroy(PathTrace *pt);
DLLEXPORT void pathtrace_append_frame(PathTrace *pt, Time time, float coord, void *other);
DLLEXPORT bool pathtrace_intersect_test_with_clearance(PathTrace *pt0, PathTrace *pt1, float clearance, float shift);
DLLEXPORT void pathtrace_boundary(PathTrace* pt, float* pmax, float* pmin);

#endif //TCY_PATH_H
