#!/usr/bin/env python3
"""Native regression checks for owner-only frame presentation gates.

Extracts the actual Blt predicate, Flip/EndScene hooks, and UI group finalizer.
COM calls and presentation publication are stubs; this is not a Windows test.
BltFast is covered by test_bitmap.py.
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
from test_drag import extract_type


def definition(source, name):
    match = re.search(r"^static [^\n]*\b" + re.escape(name) + r"\s*\([^;{}]*\)\s*\{", source, re.M)
    if not match:
        raise ValueError(f"missing actual function definition {name}")
    return extract_function(source[match.start():], name)


PREFIX = r'''
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#define WINAPI
#define MAX_UI_GROUPS 4
#define MAX_UI_FRAME_RECTS 4
typedef int32_t LONG;
typedef int32_t HRESULT;
typedef uint32_t DWORD;
typedef uint16_t WORD;
typedef uint8_t BYTE;
typedef struct { LONG left,top,right,bottom; } RECT;
'''


STUBS = r'''
static DWORD g_ui_frame_rect_count,g_owner_frame_member_count,g_owner_submit_count,g_owner_bitmap_frame_calls;
static DWORD g_ui_scenes_since_present,g_ui_present_serial;
static int g_ui_present_seen,g_ui_fallback_logged;
static LONG g_ui_screen_w=3440,g_ui_screen_h=1440,g_ui_origin_x,g_ui_origin_y;
static int g_ui_anchor_mode=1,g_ui_global_threshold_percent=65,g_ui_scale_global;
static int g_ui_group_gap=12,g_ui_stable_match_gap=96;
static DWORD g_ui_next_stable_id=1,g_ui_prev_group_count,g_ui_prev_member_count,g_ui_group_generation;
static UIRectF g_ui_frame_rects[MAX_UI_FRAME_RECTS];
static DWORD g_ui_frame_rect_hints[MAX_UI_FRAME_RECTS];
static UIGroup g_ui_prev_groups[MAX_UI_GROUPS],g_ui_build_groups[MAX_UI_GROUPS];
static UIGroupMember g_ui_prev_members[MAX_UI_FRAME_RECTS],g_ui_build_members[MAX_UI_FRAME_RECTS];
static int group_locked;
static void ui_group_lock(void) { assert(!group_locked); group_locked=1; }
static void ui_group_unlock(void) { assert(group_locked); group_locked=0; }
static void finalize_ui_frame(void);
static int boundary_calls,published,cleared,installed,logged,flip_calls,end_calls;
static void* flipped_self;
static void* flipped_override;
static DWORD flipped_flags;
static void* ended_self;
static void owner_finalize_frame(void) { ++published; }
static void clear_ui_frame_accumulator(void) {
    ++cleared; g_ui_frame_rect_count=g_owner_frame_member_count=g_owner_submit_count=g_owner_bitmap_frame_calls=0;
}
static void owner_install_active_vtables(void) { ++installed; }
static void log_line(const char* text) { (void)text; ++logged; }
static void ui_present_boundary(const char* method) {
    assert(strcmp(method,"Flip")==0); ++boundary_calls;
    g_ui_present_seen=1; ++g_ui_present_serial;
    owner_finalize_frame(); finalize_ui_frame(); clear_ui_frame_accumulator();
    g_ui_scenes_since_present=0;
}
typedef struct { int screenish,target; } FakeSurface;
static int surface_is_screenish(void* p) { return p && ((FakeSurface*)p)->screenish; }
static int is_render_target(void* p) { return p && ((FakeSurface*)p)->target; }
static HRESULT fake_flip(void* self,void* target,DWORD flags) {
    ++flip_calls; flipped_self=self; flipped_override=target; flipped_flags=flags; return 42;
}
static HRESULT fake_end(void* self) { ++end_calls; ended_self=self; return 43; }
static SurfHookRec surface_record;
static DevHookRec device_record;
static SurfHookRec* surf_rec(void* self) { (void)self; return &surface_record; }
static DevHookRec* dev_rec(void* self) { (void)self; return &device_record; }
'''


TESTS = r'''
static void reset(void) {
    assert(!group_locked);
    g_ui_frame_rect_count=g_owner_frame_member_count=g_owner_submit_count=g_owner_bitmap_frame_calls=0;
    g_ui_scenes_since_present=g_ui_present_serial=0;
    g_ui_present_seen=g_ui_fallback_logged=0;
    boundary_calls=published=cleared=installed=logged=flip_calls=end_calls=0;
    g_ui_prev_group_count=g_ui_prev_member_count=0;
    surface_record.orig_flip=(void*)fake_flip;
    device_record.orig_end_scene=(void*)fake_end;
}
static void test_blt(void) {
    FakeSurface display={1,0},render={1,1},other={1,0},small={0,0};
    RECT full={0,0,3440,1440},tiny={0,0,20,20};
    reset();
    assert(!blt_is_present(&display,0,&render,0));
    g_owner_bitmap_frame_calls=1;
    assert(blt_is_present(&display,0,&render,0));
    assert(blt_is_present(&render,0,&display,0));
    assert(blt_is_present(&display,&full,&other,&full));
    assert(!blt_is_present(&display,0,0,0));
    assert(!blt_is_present(&small,0,&render,0));
    assert(!blt_is_present(&display,0,&small,0));
    assert(!blt_is_present(&display,&tiny,&other,&full));
    assert(!blt_is_present(&display,&full,&other,&tiny));
    assert(!g_ui_frame_rect_count && !g_owner_frame_member_count && !g_owner_submit_count);
    puts("PASS: owner-only Blt frames qualify; empty, non-screen, missing-source and tiny copies do not");
}
static void test_flip_and_empty_finalize(void) {
    FakeSurface display={1,0},target={1,1};
    reset();
    assert(hook_SurfaceFlip(&display,&target,123)==42);
    assert(!boundary_calls && flip_calls==1);
    g_owner_bitmap_frame_calls=1;
    g_ui_prev_group_count=2; g_ui_prev_member_count=3;
    assert(hook_SurfaceFlip(&display,&target,123)==42);
    assert(boundary_calls==1 && published==1 && cleared==1 && flip_calls==2);
    assert(flipped_self==&display && flipped_override==&target && flipped_flags==123);
    assert(g_ui_present_serial==1 && g_ui_present_seen);
    assert(!g_ui_prev_group_count && !g_ui_prev_member_count && !group_locked);
    assert(!g_owner_bitmap_frame_calls);
    assert(hook_SurfaceFlip(&display,&target,123)==42 && boundary_calls==1);
    puts("PASS: owner-only Flip publishes once and actual empty UI finalization clears stale fallback groups");
}
static void test_end_scene(void) {
    int device;
    reset(); g_owner_bitmap_frame_calls=1; g_ui_scenes_since_present=3;
    assert(hook_EndScene(&device)==43 && !published);
    g_ui_scenes_since_present=4; g_ui_prev_group_count=2; g_ui_prev_member_count=3;
    assert(hook_EndScene(&device)==43);
    assert(published==1 && cleared==1 && installed==1 && logged==1);
    assert(g_ui_present_serial==1 && !g_ui_scenes_since_present && !g_ui_present_seen);
    assert(!g_ui_prev_group_count && !g_ui_prev_member_count);
    assert(ended_self==&device && end_calls==2);
    g_ui_scenes_since_present=4;
    assert(hook_EndScene(&device)==43 && published==1); /* empty frame */
    g_owner_bitmap_frame_calls=1; g_ui_present_seen=1;
    assert(hook_EndScene(&device)==43 && published==1); /* actual presentation already observed */
    puts("PASS: owner-only four-scene fallback publishes; shorter, empty and post-presentation scenes do not");
}
int main(void) { test_blt(); test_flip_and_empty_finalize(); test_end_scene(); return 0; }
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=Path(__file__).resolve().with_name("prm_uifix.c"))
    args = parser.parse_args()
    source = args.source.read_text()
    names = ("UIRectF", "UIGroup", "UIGroupMember", "SurfHookRec", "DevHookRec")
    types = "\n".join(extract_type(source, name) for name in names)
    for name in ("PFN_DDS7_Flip", "PFN_D3D7_EndScene"):
        match = re.search(r"^typedef[^\n]*\b" + name + r"\b[^\n]*;", source, re.M)
        if not match:
            raise ValueError(f"missing actual source typedef {name}")
        types += "\n" + match[0]
    names = ("f_abs", "rect_near", "rect_area", "rect_union", "rect_is_global", "choose_group_anchor",
             "finalize_ui_frame", "blt_is_present", "hook_SurfaceFlip", "hook_EndScene")
    functions = "\n".join(definition(source, name) for name in names)
    with tempfile.TemporaryDirectory(prefix="prm-present-test-") as directory:
        harness = Path(directory) / "present.c"
        binary = Path(directory) / "present-test"
        harness.write_text(PREFIX + types + STUBS + functions + TESTS)
        compiler = shlex.split(os.environ.get("CC", "clang"))
        subprocess.run(compiler + ["-std=c11", "-O1", "-g", "-Wall", "-Wextra", "-Werror",
                                   "-fsanitize=undefined", "-fno-sanitize-recover=all", str(harness), "-o", str(binary)], check=True)
        subprocess.run([str(binary)], check=True)
    print("PASS: native extracted presentation gates and empty-group finalization; COM/publication are stubs")


if __name__ == "__main__":
    main()
