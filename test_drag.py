#!/usr/bin/env python3
"""Test actual copied-owner capture functions with native C stubs.

This verifies transform, snapshot, and chat-title owner preparation behavior,
not Windows capture integration or live UIWindow tree traversal. The function
bodies and owner record types are extracted from prm_uifix.c at each run.
"""

import argparse
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True
from test_input import extract_function


def extract_type(source, name):
    match = re.search(r"typedef\s+struct\s*\{[^}]*\}\s*" + re.escape(name) + r"\s*;", source)
    if not match:
        raise ValueError(f"missing actual source type {name}")
    return match[0]


PREFIX = r'''
#include <assert.h>
#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
typedef int32_t LONG;
typedef uint32_t DWORD;
typedef uintptr_t ULONG_PTR;
typedef struct { LONG x,y; } POINT;
typedef struct { float l,t,r,b; } UIRectF;
'''


STUBS = r'''
static OwnerInputRegion g_owner_input_regions[16];
static OwnerCaptureLink g_owner_capture_links[16];
static OwnerWindowState g_owner_windows[8];
static OwnerBitmapScope g_owner_bitmap_scope;
static DWORD g_owner_input_region_count,g_owner_capture_link_count;
static DWORD g_owner_capture_object,g_owner_capture_root,g_ui_present_serial;
static float g_owner_capture_ax,g_owner_capture_ay;
static int g_owner_capture_native_size;
static DWORD g_owner_capture_maps,g_owner_capture_changes,g_owner_capture_unknown;
static DWORD g_owner_mapped_mouse,g_owner_input_candidates,g_owner_input_overlap_hits;
static DWORD g_owner_window_count,g_owner_bitmap_frame_calls,g_owner_bitmap_order;
static DWORD g_owner_input_order,g_owner_bitmap_unsupported;
static int g_owner_input_remap_enabled=1,g_owner_scale_enabled=1;
static int g_input_enabled=1,g_input_runtime_enabled=1,g_ui_runtime_enabled=1;
static int g_owner_bitmap_hooks_installed=1,g_owner_submit_enabled=1,g_owner_tooltip_enabled=1;
static int g_ui_scale_global=0,g_ui_anchor_mode=2,g_ui_global_threshold_percent=65;
static LONG g_ui_screen_w=3440,g_ui_screen_h=1440,g_ui_origin_x=0,g_ui_origin_y=0;
static DWORD fake_capture;
static float scale=1.25f;
static int locked;
static void owner_input_region_lock(void) { assert(!locked); locked=1; }
static void owner_input_region_unlock(void) { assert(locked); locked=0; }
static float ui_scale_factor(void) { return scale; }
static DWORD owner_native_capture(void) { return fake_capture; }
static DWORD current_thread(void) { return 17; }
static DWORD (*g_GetCurrentThreadId)(void)=current_thread;
static OwnerWindowState* owner_state_for(DWORD object,int create) {
    DWORD i;
    for(i=0;i<g_owner_window_count;++i)
        if(g_owner_windows[i].object_ptr==object) return &g_owner_windows[i];
    if(!create || !object || g_owner_window_count>=8) return 0;
    memset(&g_owner_windows[g_owner_window_count],0,sizeof(g_owner_windows[0]));
    g_owner_windows[g_owner_window_count].object_ptr=object;
    g_owner_windows[g_owner_window_count].vtable_ptr=0x50000000UL+g_owner_window_count;
    return &g_owner_windows[g_owner_window_count++];
}
'''


TESTS = r'''
static void reset(void) {
    assert(!locked);
    memset(g_owner_input_regions,0,sizeof(g_owner_input_regions));
    memset(g_owner_capture_links,0,sizeof(g_owner_capture_links));
    memset(g_owner_windows,0,sizeof(g_owner_windows));
    memset(&g_owner_bitmap_scope,0,sizeof(g_owner_bitmap_scope));
    g_owner_window_count=g_owner_bitmap_frame_calls=g_owner_bitmap_order=0;
    g_owner_input_order=g_owner_bitmap_unsupported=0;
    g_owner_bitmap_hooks_installed=g_owner_submit_enabled=g_owner_tooltip_enabled=1;
    g_ui_scale_global=0; g_ui_anchor_mode=2;
    g_owner_input_region_count=g_owner_capture_link_count=0;
    g_owner_capture_object=g_owner_capture_root=0;
    g_owner_capture_native_size=0;
    g_owner_capture_maps=g_owner_capture_changes=g_owner_capture_unknown=0;
    g_ui_present_serial=100; fake_capture=0; scale=1.25f;
    g_owner_input_remap_enabled=g_owner_scale_enabled=1;
    g_input_enabled=g_input_runtime_enabled=g_ui_runtime_enabled=1;
}
static void region(unsigned int index,DWORD object,DWORD present,float ax,float ay) {
    OwnerInputRegion* r=&g_owner_input_regions[index];
    r->object_ptr=object; r->present=present; r->ax=ax; r->ay=ay;
    r->native_size=0;
    r->rect=(UIRectF){100,100,300,300}; r->input_order=index+1;
    if(g_owner_input_region_count<=index) g_owner_input_region_count=index+1;
}
static void alias(DWORD child,DWORD root,DWORD present) {
    g_owner_capture_links[g_owner_capture_link_count++]=(OwnerCaptureLink){child,root,present};
}
static void point_is(POINT p,LONG x,LONG y) { assert(p.x==x && p.y==y); assert(!locked); }
static void test_capture_lifetime(void) {
    reset(); region(0,10,100,1720,720);
    POINT p={-1000,2400};
    assert(owner_input_map_capture(&p,10)); point_is(p,-456,2064);
    assert(g_owner_capture_root==10 && g_owner_capture_object==10);
    g_owner_input_region_count=0; g_ui_present_serial=200;
    p=(POINT){-1000,2400};
    assert(owner_input_map_capture(&p,10)); point_is(p,-456,2064);
    region(0,10,200,0,0); /* rebuilt snapshots cannot change an active drag */
    p=(POINT){-1000,2400};
    assert(owner_input_map_capture(&p,10)); point_is(p,-456,2064);
    p=(POINT){123,456};
    assert(!owner_input_map_capture(&p,0)); point_is(p,123,456);
    assert(!g_owner_capture_root && !g_owner_capture_object);
    region(1,20,200,0,0);
    p=(POINT){1000,2000};
    assert(owner_input_map_capture(&p,20)); point_is(p,800,1600);
    p=(POINT){123,456};
    assert(!owner_input_map_capture(&p,999)); point_is(p,123,456);
    assert(g_owner_capture_object==999 && !g_owner_capture_root);
    puts("PASS: captured roots remain stable outside bounds and across snapshots; release/change/unknown capture reset ownership");
}
static void test_aliases_and_age(void) {
    reset(); region(0,10,98,1720,720); alias(11,10,98);
    POINT p={-1000,2400};
    assert(owner_input_map_capture(&p,11)); point_is(p,-456,2064);
    g_owner_capture_link_count=g_owner_input_region_count=0;
    p=(POINT){-1000,2400};
    assert(owner_input_map_capture(&p,11)); point_is(p,-456,2064);
    reset(); region(0,10,97,1720,720); alias(11,10,100);
    p=(POINT){123,456};
    assert(!owner_input_map_capture(&p,10)); point_is(p,123,456);
    assert(!owner_input_map_capture(&p,11)); point_is(p,123,456);
    g_owner_input_regions[0].present=98;
    assert(owner_input_map_capture(&p,11)); /* same pending capture can resolve after publication */
    reset(); region(0,10,100,1720,720); alias(11,10,97);
    p=(POINT){123,456};
    assert(!owner_input_map_capture(&p,11)); point_is(p,123,456);
    reset(); region(0,10,100,1720,720); region(1,11,100,0,0); alias(11,10,100);
    p=(POINT){1000,2000};
    assert(owner_input_map_capture(&p,11)); point_is(p,800,1600); /* direct root beats alias */
    reset(); g_ui_present_serial=1;
    region(0,10,UINT32_MAX,1720,720); alias(11,10,UINT32_MAX);
    p=(POINT){-1000,2400};
    assert(owner_input_map_capture(&p,11)); point_is(p,-456,2064);
    owner_input_map_capture(&p,0);
    g_owner_input_regions[0].present=UINT32_MAX-1;
    p=(POINT){123,456};
    assert(!owner_input_map_capture(&p,10)); point_is(p,123,456);
    g_owner_input_regions[0].present=2; /* future record is not a valid previous snapshot */
    assert(!owner_input_map_capture(&p,10)); point_is(p,123,456);
    puts("PASS: child aliases, two-present freshness, stale rejection, wraparound, and direct-root priority");
}
static void test_drag_delta_and_gates(void) {
    reset(); scale=1.33f;
    POINT start={1000,600},mapped_start=start;
    assert(owner_input_apply_transform(&mapped_start,1720,720));
    for(int delta=-1000;delta<=1000;++delta) {
        POINT moved={start.x+delta,start.y-delta};
        assert(owner_input_apply_transform(&moved,1720,720));
        float visual_dx=(moved.x-mapped_start.x)*scale;
        float visual_dy=(moved.y-mapped_start.y)*scale;
        assert(fabsf(visual_dx-delta)<=scale+0.001f);
        assert(fabsf(visual_dy+delta)<=scale+0.001f);
    }
    scale=0; POINT p={123,456};
    assert(!owner_input_apply_transform(&p,1720,720)); point_is(p,123,456);
    assert(!owner_input_apply_transform(0,1720,720));
    int* gates[]={&g_owner_input_remap_enabled,&g_owner_scale_enabled,&g_input_enabled,
                  &g_input_runtime_enabled,&g_ui_runtime_enabled};
    for(unsigned int i=0;i<sizeof(gates)/sizeof(gates[0]);++i) {
        reset(); region(0,10,100,1720,720); fake_capture=10;
        p=(POINT){-1000,2400}; assert(remap_owner_point(&p));
        *gates[i]=0; p=(POINT){123,456};
        assert(!remap_owner_point(&p)); point_is(p,123,456);
        assert(!g_owner_capture_object && !g_owner_capture_root);
    }
    reset(); region(0,10,98,0,0); p=(POINT){200,200};
    assert(remap_owner_point(&p)); point_is(p,160,160);
    g_owner_input_regions[0].present=97; p=(POINT){200,200};
    assert(!remap_owner_point(&p)); point_is(p,200,200);
    reset(); region(0,10,100,0,0); fake_capture=999; p=(POINT){200,200};
    DWORD maps_before=g_owner_mapped_mouse;
    assert(remap_owner_point(&p)); point_is(p,200,200);
    assert(!g_owner_capture_root && g_owner_capture_unknown==1);
    assert(g_owner_mapped_mouse==maps_before); /* handled raw; other-owner/fallback remapping must stop */
    alias(999,10,97); p=(POINT){200,200};
    assert(remap_owner_point(&p)); point_is(p,200,200);
    assert(!g_owner_capture_root && g_owner_mapped_mouse==maps_before);
    puts("PASS: physical 1:1 drag deltas within integer rounding; disabled modes clear capture; ordinary snapshot grace");
    puts("PASS: unresolved native capture preserves raw coordinates and suppresses ordinary/fallback remapping");
}
static void native_map(unsigned int index,DWORD object) {
    region(index,object,g_ui_present_serial,1720,720);
    g_owner_input_regions[index].rect=(UIRectF){0,0,3440,1440};
    g_owner_input_regions[index].native_size=1;
}
static void test_native_map_overlap(void) {
    POINT p;
    reset(); region(0,10,100,0,0); native_map(1,20);
    p=(POINT){200,200}; assert(remap_owner_point(&p)); point_is(p,200,200);
    /* Bitmap preparation publishes exact order for both native and scaled
       owners, so the later native map keeps the stronger overlap hint too. */
    g_owner_input_regions[0].exact_order=9;
    g_owner_input_regions[1].exact_order=10;
    p=(POINT){200,200}; assert(remap_owner_point(&p)); point_is(p,200,200);
    /* A later dialog remains interactive above the map. */
    region(2,30,100,0,0);
    g_owner_input_regions[2].exact_order=11;
    p=(POINT){200,200}; assert(remap_owner_point(&p)); point_is(p,160,160);
    for(unsigned int i=0;i<3;++i) g_owner_input_regions[i].exact_order=0;
    p=(POINT){200,200}; assert(remap_owner_point(&p)); point_is(p,160,160);
    /* The map's native rectangle is used as-is, including both screen corners. */
    p=(POINT){0,0}; assert(remap_owner_point(&p)); point_is(p,0,0);
    p=(POINT){3439,1439}; assert(remap_owner_point(&p)); point_is(p,3439,1439);
    p=(POINT){3441,1441}; assert(!remap_owner_point(&p)); point_is(p,3441,1441);
    puts("PASS: native map occludes older scaled HUD, later dialogs win, and native screen bounds stay unchanged");
}
static void test_native_capture_lifetime(void) {
    POINT p;
    reset(); native_map(0,20); alias(21,20,100); fake_capture=21;
    p=(POINT){-1000,2400}; assert(remap_owner_point(&p)); point_is(p,-1000,2400);
    assert(g_owner_capture_object==21 && g_owner_capture_root==20 && g_owner_capture_native_size);
    g_owner_input_region_count=g_owner_capture_link_count=0; g_ui_present_serial=200;
    p=(POINT){4000,-300}; assert(remap_owner_point(&p)); point_is(p,4000,-300);
    region(0,20,200,0,0); /* Rebuilt root now scaled; the ongoing capture keeps its original identity. */
    p=(POINT){-1000,2400}; assert(remap_owner_point(&p)); point_is(p,-1000,2400);
    assert(g_owner_capture_native_size);
    fake_capture=0; p=(POINT){-1000,2400};
    assert(!remap_owner_point(&p)); point_is(p,-1000,2400);
    assert(!g_owner_capture_object && !g_owner_capture_root && !g_owner_capture_native_size);
    fake_capture=20; p=(POINT){1000,2000};
    assert(remap_owner_point(&p)); point_is(p,800,1600);
    assert(!g_owner_capture_native_size); /* New capture takes the new scaled transform. */
    native_map(1,30); fake_capture=30; p=(POINT){1000,2000};
    assert(remap_owner_point(&p)); point_is(p,1000,2000);
    assert(g_owner_capture_native_size);
    fake_capture=999; p=(POINT){1000,2000};
    assert(remap_owner_point(&p)); point_is(p,1000,2000);
    assert(!g_owner_capture_root && !g_owner_capture_native_size);
    puts("PASS: native child capture freezes identity beyond bounds and rebuilt snapshots; release/change reset its mode");
}
static void test_native_capture_toggles(void) {
    int* gates[]={&g_owner_input_remap_enabled,&g_owner_scale_enabled,&g_input_enabled,
                  &g_input_runtime_enabled,&g_ui_runtime_enabled};
    POINT p;
    for(unsigned int i=0;i<sizeof(gates)/sizeof(gates[0]);++i) {
        reset(); native_map(0,20); fake_capture=20;
        p=(POINT){-1000,2400}; assert(remap_owner_point(&p)); point_is(p,-1000,2400);
        assert(g_owner_capture_native_size);
        *gates[i]=0; p=(POINT){123,456};
        assert(!remap_owner_point(&p)); point_is(p,123,456);
        assert(!g_owner_capture_object && !g_owner_capture_root && !g_owner_capture_native_size);
        *gates[i]=1; region(0,20,100,0,0); p=(POINT){1000,2000};
        assert(remap_owner_point(&p)); point_is(p,800,1600);
        assert(!g_owner_capture_native_size);
    }
    puts("PASS: every input/scaling toggle clears native capture; re-enabling picks up the current transform");
}

/* Snapshot publication is a fixture here: production preparation supplies its
   bounds/anchor/orders, and the actual remapper consumes the copied record.
   test_capture.py independently checks the real publication call and loop. */
static void publish_prepared(unsigned int index,OwnerWindowState* st) {
    OwnerInputRegion* r=&g_owner_input_regions[index];
    assert(st && st->last_input_order);
    r->rect=st->input_local_bbox;
    r->rect.l+=st->pos_x; r->rect.r+=st->pos_x;
    r->rect.t+=st->pos_y; r->rect.b+=st->pos_y;
    r->ax=st->ax; r->ay=st->ay; r->object_ptr=st->object_ptr;
    r->present=g_ui_present_serial; r->input_order=st->last_input_order;
    r->exact_order=st->last_draw_order; r->native_size=0;
    if(g_owner_input_region_count<=index) g_owner_input_region_count=index+1;
}
static void test_moving_title_input(void) {
    OwnerWindowState *title,*dialog; POINT p;
    reset(); scale=1.33f;
    title=owner_state_for(10,1); strcpy(title->class_name,"UIChatRoomTitle");
    assert(owner_bitmap_prepare(10,500,250,140,34));
    assert(title->ax==570 && title->ay==284 && title->last_input_order);
    publish_prepared(0,title);
    /* This point is outside both native left/top edges, but inside the scaled
       title. The old unowned/ordinary-anchor paths cannot select it correctly. */
    p=(POINT){480,242}; assert(remap_owner_point(&p)); point_is(p,502,252);
    p=(POINT){570,284}; assert(remap_owner_point(&p)); point_is(p,570,284);
    p=(POINT){476,250}; assert(!remap_owner_point(&p)); point_is(p,476,250);
    p=(POINT){570,285}; assert(!remap_owner_point(&p)); point_is(p,570,285);
    ++g_ui_present_serial;
    assert(owner_bitmap_prepare(10,1500,550,140,34)); publish_prepared(0,title);
    p=(POINT){1480,542}; assert(remap_owner_point(&p)); point_is(p,1502,552);
    p=(POINT){480,242}; assert(!remap_owner_point(&p)); point_is(p,480,242);
    p=(POINT){1570,584}; assert(remap_owner_point(&p)); point_is(p,1570,584);
    /* Exact draw order remains decisive when a normal dialog overlaps. */
    assert(owner_bitmap_prepare(10,500,250,140,34)); publish_prepared(0,title);
    dialog=owner_state_for(20,1); strcpy(dialog->class_name,"UIItemWnd");
    g_ui_anchor_mode=0;
    assert(owner_bitmap_prepare(20,400,175,150,100)); publish_prepared(1,dialog);
    p=(POINT){570,260}; assert(remap_owner_point(&p)); point_is(p,429,195);
    assert(owner_bitmap_prepare(10,500,250,140,34)); publish_prepared(0,title);
    p=(POINT){570,260}; assert(remap_owner_point(&p)); point_is(p,570,266);
    assert(!g_owner_capture_unknown && !g_owner_bitmap_unsupported);
    puts("PASS: actual title preparation and remapping select enlarged edges, preserve pointer attachment, follow movement, and respect dialog draw order");
}
static void test_minimap_input(void) {
    const float factors[]={1.33f,2.0f}; unsigned int i; POINT p,screen;
    for(i=0;i<2;++i) {
        OwnerWindowState* mini;
        reset(); scale=factors[i]; g_ui_anchor_mode=1;
        mini=owner_state_for(10,1); strcpy(mini->class_name,"UIMinimapZoomWnd");
        assert(owner_bitmap_prepare(10,3295,17,128,140)); publish_prepared(0,mini);
        assert(mini->ax==3440 && mini->ay==0);
        /* Enlarged controls are outside the old native window, but the same
           owner transform maps their screen position back to the real button. */
        screen.x=(LONG)(3440+(3350-3440)*scale+0.5f);
        screen.y=(LONG)(151*scale+0.5f); p=screen;
        assert(remap_owner_point(&p)); point_is(p,3350,151);
        /* A map-image point follows that identical input transform. */
        p.x=(LONG)(3440+(3360-3440)*scale+0.5f);
        p.y=(LONG)(50*scale+0.5f);
        assert(remap_owner_point(&p)); point_is(p,3360,50);
        /* Native capture of a child keeps the minimap's root transform. */
        alias(11,10,g_ui_present_serial); fake_capture=11; p=screen;
        assert(remap_owner_point(&p)); point_is(p,3350,151);
        assert(g_owner_capture_root==10 && !g_owner_capture_unknown);
        fake_capture=0; p=(POINT){1700,700};
        assert(!remap_owner_point(&p)); point_is(p,1700,700);
    }
    puts("PASS: minimap image/controls and captured children map to native coordinates at 133% and 200%; outside points stay raw");
}
int main(void) {
    test_capture_lifetime(); test_aliases_and_age(); test_drag_delta_and_gates();
    test_native_map_overlap(); test_native_capture_lifetime(); test_native_capture_toggles();
    test_moving_title_input(); test_minimap_input();
    return 0;
}
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=Path(__file__).resolve().with_name("prm_uifix.c"))
    args = parser.parse_args()
    source = args.source.read_text()
    types = "\n".join(extract_type(source, name) for name in (
        "OwnerWindowState", "OwnerInputRegion", "OwnerCaptureLink", "OwnerBitmapScope"))
    functions = "\n".join(extract_function(source, name) for name in (
        "s_len", "s_contains", "s_equal", "owner_class_is_hover_popup",
        "owner_class_is_world_label", "owner_class_is_world_title", "owner_class_is_world_name", "rect_is_global", "choose_group_anchor",
        "owner_input_touch_state", "owner_bitmap_prepare",
        "rect_contains_point", "rect_area", "transform_bounds", "owner_input_apply_transform",
        "owner_input_map_capture", "remap_owner_point"))
    with tempfile.TemporaryDirectory(prefix="prm-drag-test-") as directory:
        harness = Path(directory) / "drag.c"
        binary = Path(directory) / "drag-test"
        harness.write_text(PREFIX + types + STUBS + functions + TESTS)
        compiler = shlex.split(os.environ.get("CC", "clang"))
        subprocess.run(compiler + ["-std=c11", "-O1", "-g", "-Wall", "-Wextra", "-Werror",
                                   "-fsanitize=undefined", "-fno-sanitize-recover=all", str(harness), "-o", str(binary)], check=True)
        subprocess.run([str(binary)], check=True)
    print("PASS: extracted capture/drag functions with native stubs; no Windows integration claim")


if __name__ == "__main__":
    main()
