//
// Created by tefx on 10/23/19.
//

#include "../include/path.h"
#include "../include/cd.h"
#include <stdlib.h>
#include <float.h>
#include <math.h>

PathFrameChunk *pathframechunk_create(int chunk_size) {
    PathFrameChunk *chunk = (PathFrameChunk *) malloc(sizeof(PathFrameChunk));
    chunk->num = 0;
    chunk->frames = (PathKeyFrame *) malloc(sizeof(PathKeyFrame) * chunk_size);
    chunk->next = NULL;
    return chunk;
}

void pathframechunk_free(PathFrameChunk *chunk) {
    free(chunk->frames);
    free(chunk);
}

void pathtrace_init(PathTrace *pt, int chunk_size) {
    pt->chunk_size = chunk_size;
    pt->chunks = pt->last_chunk = pathframechunk_create(chunk_size);
    pt->max = -FLT_MAX;
    pt->min = FLT_MAX;
//    printf("PT0, %f %f\n", pt->max, pt->min);
}

void pathtrace_destroy(PathTrace *pt) {
    PathFrameChunk *chunk = pt->chunks;
    PathFrameChunk *tmp;
    while (chunk) {
        tmp = chunk;
        chunk = chunk->next;
        pathframechunk_free(tmp);
    }
}

PathFrameChunk *pathtrace_append_chunk(PathTrace *pt) {
    PathFrameChunk *chunk = pathframechunk_create(pt->chunk_size);
    pt->last_chunk->next = chunk;
    pt->last_chunk = chunk;
    return chunk;
}

static inline PathKeyFrame *pathtrace_last_frame(PathTrace *pt) {
    PathFrameChunk *chunk = pt->last_chunk;
    if (chunk->num > 0)
        return chunk->frames + chunk->num - 1;
    else
        return NULL;
}


static inline bool pathframechunk_frame_values(PathFrameChunk *chunk, int i, Time_TCY *time, double *coord, void **other) {
    PathKeyFrame *frame;
    while (i >= chunk->num) {
        i -= chunk->num;
        chunk = chunk->next;
        if (chunk == NULL)
            return FALSE;
    }
    frame = chunk->frames + i;
    if (time != NULL) *time = frame->time;
    if (coord != NULL) *coord = frame->coord;
    if (other != NULL) *other = frame->other;
    return TRUE;
}

static inline bool pathtrace_last_frame_values(PathTrace *pt, Time_TCY *time, double *coord, void **other) {
    PathFrameChunk *chunk = pt->last_chunk;
    if (chunk->num > 0) {
        pathframechunk_frame_values(chunk, chunk->num - 1, time, coord, other);
        return TRUE;
    } else {
        return FALSE;
    }
}

static inline bool pathtrace_is_last_frame(PathTrace *pt, PathFrameChunk *pfc, int idx) {
    return pt->last_chunk == pfc && pfc->num == idx + 1;
}

void pathtrace_append_frame(PathTrace *pt, Time_TCY time, double coord, void *other) {
    PathFrameChunk *chunk = pt->last_chunk;
    PathKeyFrame *frame;
    Time_TCY last_time = -1;

    pathtrace_last_frame_values(pt, &last_time, NULL, NULL);
    if (fne(time, last_time)) {
        if (chunk->num == pt->chunk_size)
            chunk = pathtrace_append_chunk(pt);
        frame = chunk->frames + (chunk->num++);
        frame->time = time;
        frame->coord = coord;
        frame->other = other;
        pt->max = fmaxf(pt->max, coord);
        pt->min = fminf(pt->min, coord);
//        printf("PT, %f %f\n", pt->max, pt->min);
    }
}


bool pathtrace_intersect_test_with_clearance(PathTrace *pt0, PathTrace *pt1, double clearance, double shift) {
    int i = 0, j = 0;
    PathFrameChunk *pfc0 = pt0->chunks;
    PathFrameChunk *pfc1 = pt1->chunks;
    Time_TCY x1 = 0, x2 = 0, x3 = 0, x4 = 0;
    double y1 = 0, y2 = 0, y3 = 0, y4 = 0;
    Time_TCY et0 = 0, et1 = 0;

    pathtrace_last_frame_values(pt0, &et0, NULL, NULL);
    pathtrace_last_frame_values(pt1, &et1, NULL, NULL);

    while ((!pathtrace_is_last_frame(pt0, pfc0, j - 1)) &&
           (!pathtrace_is_last_frame(pt1, pfc1, i - 1))) {

        pathframechunk_frame_values(pfc1, i, &x1, &y1, NULL);
        if (pathtrace_is_last_frame(pt1, pfc1, i)) {
//            x2 = et0 > et1 ? et0 : et1;
            x2 = flt(et1, et0) ? et0 : et1;
            y2 = y1;
        } else {
            pathframechunk_frame_values(pfc1, i + 1, &x2, &y2, NULL);
        }

        pathframechunk_frame_values(pfc0, j, &x3, &y3, NULL);
        if (pathtrace_is_last_frame(pt0, pfc0, j)) {
//            x4 = et0 > et1 ? et0 : et1;
            x4 = flt(et1, et0) ? et0 : et1;
            y4 = y3;
        } else {
            pathframechunk_frame_values(pfc0, j + 1, &x4, &y4, NULL);
        }

        y3 += shift;
        y4 += shift;

//            printf("(%f,%f), (%f, %f), (%f,%f), (%f,%f)\n", (float)x3, y3, (float)x4, y4, (float)x1, y1, (float)x2, y2);
        if (flt(x2, x3)) i++;
        else if (flt(x4, x1)) j++;
        else if (cross_test_with_clearance(x1, y1, x2, y2, x3, y3, x4, y4, clearance)) {
            return TRUE;
        }
        else if (flt(x2,x4)) i++;
        else j++;
    }
    return FALSE;
}

void pathtrace_boundary(PathTrace *pt, double *pmax, double *pmin) {
    PathFrameChunk *chunk = pt->chunks;
    if (pmax) *pmax = FLT_MIN;
    if (pmin) *pmin = FLT_MAX;

    while (chunk) {
        for (int i = 0; i < chunk->num; ++i) {
            if (pmax) *pmax = fmaxf(chunk->frames[i].coord, *pmax);
            if (pmin) *pmin = fminf(chunk->frames[i].coord, *pmin);
        }
        chunk = chunk->next;
    }
}
