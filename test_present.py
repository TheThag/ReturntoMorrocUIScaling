#!/usr/bin/env python3
"""Native regression checks for frame presentation and the in-game settings overlay.

Extracts the actual Blt/BltFast/Flip hooks, presentation gates, and settings
surface helpers. DirectDraw COM calls and GDI drawing are represented by
32-bit ABI-compatible fixtures; this is not a Windows rendering test.
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
#define WINAPI __attribute__((stdcall))
#define MAX_UI_GROUPS 4
#define MAX_UI_FRAME_RECTS 4
typedef int32_t LONG;
typedef int32_t HRESULT;
typedef uint32_t DWORD;
typedef uint16_t WORD;
typedef uint8_t BYTE;
typedef uint32_t ULONG;
typedef uintptr_t ULONG_PTR;
typedef uint32_t SIZE_T;
typedef uint32_t HWND;
typedef void *HDC;
typedef struct { LONG left,top,right,bottom; } RECT;
typedef struct { DWORD dwCaps,dwCaps2,dwCaps3,dwCaps4; } DDSCAPS2;
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
static volatile LONG g_ui_settings_panel_open;
static void ui_group_lock(void) { assert(!group_locked); group_locked=1; }
static void ui_group_unlock(void) { assert(group_locked); group_locked=0; }
static void finalize_ui_frame(void);
static int boundary_calls,published,cleared,installed,logged,flip_calls,end_calls;
static int blt_calls,bltfast_calls;
static int overlay_calls,overlay_before_original;
static int draw_failed_calls;
static void *overlay_surface;
static void* flipped_self;
static void* flipped_override;
static DWORD flipped_flags;
static void* ended_self;
static void *blt_self,*blt_src,*blt_dst_arg,*blt_src_rect_arg,*blt_fx_arg;
static DWORD blt_flags;
static void *bltfast_self,*bltfast_src,*bltfast_src_rect_arg;
static DWORD bltfast_x,bltfast_y,bltfast_flags;
static void owner_finalize_frame(void) { ++published; }
static void clear_ui_frame_accumulator(void) {
    ++cleared; g_ui_frame_rect_count=g_owner_frame_member_count=g_owner_submit_count=g_owner_bitmap_frame_calls=0;
}
static void owner_install_active_vtables(void) { ++installed; }
static void log_line(const char* text) { (void)text; ++logged; }
static void ui_present_boundary(const char* method) {
    assert(!strcmp(method,"Flip") || !strcmp(method,"Blt") || !strcmp(method,"BltFast")); ++boundary_calls;
    g_ui_present_seen=1; ++g_ui_present_serial;
    owner_finalize_frame(); finalize_ui_frame(); clear_ui_frame_accumulator();
    g_ui_scenes_since_present=0;
}
typedef struct FakeSurface FakeSurface;
struct FakeSurface {
    void **vt;
    DWORD w,h;
    int target;
    DWORD caps;
    HRESULT desc_result,caps_result,attached_result;
    FakeSurface *attached;
    int desc_calls,caps_calls,attached_calls,release_calls;
};
static HRESULT WINAPI fake_surface_desc(void *self,void *desc) {
    FakeSurface *s=(FakeSurface*)self;
    ++s->desc_calls;
    if(s->desc_result<0) return s->desc_result;
    *(DWORD*)((BYTE*)desc+8)=s->h;
    *(DWORD*)((BYTE*)desc+12)=s->w;
    return s->desc_result;
}
static HRESULT WINAPI fake_get_attached(void *self,void *caps_ptr,void **out) {
    FakeSurface *s=(FakeSurface*)self;
    DDSCAPS2 *caps=(DDSCAPS2*)caps_ptr;
    ++s->attached_calls;
    assert(caps && caps->dwCaps==0x4UL && caps->dwCaps2==0 && caps->dwCaps3==0 && caps->dwCaps4==0);
    if(out) *out=s->attached;
    return s->attached_result;
}
static HRESULT WINAPI fake_get_caps(void *self,void *caps) {
    FakeSurface *s=(FakeSurface*)self;
    ++s->caps_calls;
    if(s->caps_result<0) return s->caps_result;
    *(DWORD*)caps=s->caps;
    return s->caps_result;
}
static ULONG WINAPI fake_release(void *self) {
    FakeSurface *s=(FakeSurface*)self;
    ++s->release_calls;
    return 1;
}
static void surface_vtable(void **vt) {
    unsigned int i;
    for(i=0;i<27;++i) vt[i]=0;
    vt[2]=(void*)fake_release;
    vt[12]=(void*)fake_get_attached;
    vt[14]=(void*)fake_get_caps;
    vt[22]=(void*)fake_surface_desc;
}
static void surface_init(FakeSurface *s,void **vt,DWORD w,DWORD h,int target) {
    memset(s,0,sizeof(*s)); s->vt=vt; s->w=w; s->h=h; s->target=target;
    s->caps=target?0:0x00000200UL;
    s->desc_result=0; s->caps_result=0; s->attached_result=0;
}
static int is_render_target(void* p) { return p && ((FakeSurface*)p)->target; }
static HRESULT WINAPI fake_flip(void* self,void* target,DWORD flags) {
    ++flip_calls; flipped_self=self; flipped_override=target; flipped_flags=flags;
    if(overlay_calls) overlay_before_original=1;
    return 42;
}
static HRESULT WINAPI fake_end(void* self) { ++end_calls; ended_self=self; return 43; }
static HRESULT WINAPI fake_blt(void *self,RECT *dst,void *src,RECT *src_rect,DWORD flags,void *fx) {
    ++blt_calls; blt_self=self; blt_src=src; blt_dst_arg=dst; blt_src_rect_arg=src_rect; blt_flags=flags; blt_fx_arg=fx;
    if(overlay_calls) overlay_before_original=1;
    return 41;
}
static HRESULT WINAPI fake_bltfast(void *self,DWORD x,DWORD y,void *src,RECT *src_rect,DWORD flags) {
    ++bltfast_calls; bltfast_self=self; bltfast_x=x; bltfast_y=y; bltfast_src=src; bltfast_src_rect_arg=src_rect; bltfast_flags=flags;
    if(overlay_calls) overlay_before_original=1;
    return 40;
}
static int ui_settings_is_open(void) {
    return __atomic_load_n(&g_ui_settings_panel_open,__ATOMIC_ACQUIRE)!=0;
}
static void ui_settings_draw_surface(void *target) {
    ++overlay_calls; overlay_surface=target;
}
static void ui_settings_draw_failed(void) {
    ++draw_failed_calls;
    __atomic_store_n(&g_ui_settings_panel_open,0,__ATOMIC_RELEASE);
}
static int mem_readable(const void *p,DWORD bytes) { return p && bytes; }
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
    blt_calls=bltfast_calls=overlay_calls=overlay_before_original=0;
    draw_failed_calls=0;
    overlay_surface=0;
    blt_self=blt_src=blt_dst_arg=blt_src_rect_arg=blt_fx_arg=0;
    blt_flags=0; bltfast_self=bltfast_src=bltfast_src_rect_arg=0;
    bltfast_x=bltfast_y=bltfast_flags=0;
    g_ui_settings_panel_open=0;
    g_ui_prev_group_count=g_ui_prev_member_count=0;
    surface_record.orig_flip=(void*)fake_flip;
    surface_record.orig_blt=(void*)fake_blt;
    surface_record.orig_bltfast=(void*)fake_bltfast;
    device_record.orig_end_scene=(void*)fake_end;
}
static void setup_surfaces(FakeSurface *display,FakeSurface *render,FakeSurface *small,
                           FakeSurface *other,void **display_vt,void **render_vt,
                           void **small_vt,void **other_vt) {
    surface_vtable(display_vt); surface_vtable(render_vt);
    surface_vtable(small_vt); surface_vtable(other_vt);
    surface_init(display,display_vt,3440,1440,0);
    surface_init(render,render_vt,3440,1440,1);
    surface_init(small,small_vt,1280,720,0);
    surface_init(other,other_vt,3440,1440,0);
}
static void test_blt(void) {
    FakeSurface display,render,small,other;
    void *display_vt[27],*render_vt[27],*small_vt[27],*other_vt[27];
    RECT full={0,0,3440,1440},tiny={0,0,20,20};
    setup_surfaces(&display,&render,&small,&other,display_vt,render_vt,small_vt,other_vt);
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
    FakeSurface display,target,small;
    void *display_vt[27],*target_vt[27],*small_vt[27];
    surface_vtable(display_vt); surface_vtable(target_vt); surface_vtable(small_vt);
    surface_init(&display,display_vt,3440,1440,0);
    surface_init(&target,target_vt,3440,1440,1);
    surface_init(&small,small_vt,1280,720,1);
    display.attached=&target;
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
static void test_flip_settings_overlay(void) {
    FakeSurface display,target,small;
    void *display_vt[27],*target_vt[27],*small_vt[27];
    surface_vtable(display_vt); surface_vtable(target_vt); surface_vtable(small_vt);
    surface_init(&display,display_vt,3440,1440,0);
    surface_init(&target,target_vt,3440,1440,1);
    surface_init(&small,small_vt,1280,720,1);
    display.attached=&target;

    reset();
    g_ui_settings_panel_open=1; g_owner_bitmap_frame_calls=1;
    assert(hook_SurfaceFlip(&display,&target,0x1234)==42);
    assert(boundary_calls==1 && flip_calls==1);
    assert(overlay_calls==1 && overlay_surface==&target && overlay_before_original);
    assert(display.attached_calls==0 && target.release_calls==0);
    assert(flipped_self==&display && flipped_override==&target && flipped_flags==0x1234);

    reset(); display.attached_calls=display.release_calls=target.release_calls=0;
    g_ui_settings_panel_open=1; g_owner_bitmap_frame_calls=1;
    assert(hook_SurfaceFlip(&display,0,0x2345)==42);
    assert(overlay_calls==1 && overlay_surface==&target && overlay_before_original);
    assert(display.attached_calls==1 && target.release_calls==1);
    assert(flipped_self==&display && !flipped_override && flipped_flags==0x2345);

    reset(); display.attached_calls=target.release_calls=0;
    g_ui_settings_panel_open=1; display.attached_result=-1; g_owner_bitmap_frame_calls=1;
    assert(hook_SurfaceFlip(&display,0,0x3456)==42);
    assert(overlay_calls==0 && display.attached_calls==1 && target.release_calls==0);

    reset(); display.attached=&display; display.attached_result=0; display.attached_calls=display.release_calls=0;
    g_ui_settings_panel_open=1; g_owner_bitmap_frame_calls=1;
    assert(hook_SurfaceFlip(&display,0,0x3a56)==42);
    assert(overlay_calls==0 && display.attached_calls==1 && display.release_calls==1 && draw_failed_calls==1);
    display.attached=&target;

    reset(); display.attached_result=0; display.attached_calls=0; target.release_calls=0; g_owner_bitmap_frame_calls=1;
    assert(hook_SurfaceFlip(&display,&target,0x4567)==42);
    assert(overlay_calls==0 && display.attached_calls==0 && target.release_calls==0);

    reset(); g_ui_settings_panel_open=1; g_owner_bitmap_frame_calls=1;
    assert(hook_SurfaceFlip(&target,0,0x5678)==42);
    assert(overlay_calls==0 && target.release_calls==0 && draw_failed_calls==1);

    reset(); small.attached=&target; g_ui_settings_panel_open=1; g_owner_bitmap_frame_calls=1;
    assert(hook_SurfaceFlip(&small,0,0x6789)==42);
    assert(overlay_calls==0 && small.attached_calls==0 && draw_failed_calls==1);
    puts("PASS: Flip settings overlay prefers explicit backbuffer, queries slot12 with caps 0x4, releases slot2, and forwards/order-preserves original");
}
static void test_blt_settings_overlay(void) {
    FakeSurface display,render,small,other;
    void *display_vt[27],*render_vt[27],*small_vt[27],*other_vt[27];
    RECT full={0,0,3440,1440},partial={0,0,3000,1300};
    void *fx=(void*)(uintptr_t)0x7654;
    setup_surfaces(&display,&render,&small,&other,display_vt,render_vt,small_vt,other_vt);
    small.target=1;

    reset(); g_ui_settings_panel_open=1; g_owner_bitmap_frame_calls=1;
    assert(hook_SurfaceBlt(&display,&full,&render,&full,0x55,fx)==41);
    assert(boundary_calls==1 && blt_calls==1);
    assert(overlay_calls==1 && overlay_surface==&render && overlay_before_original);
    assert(blt_self==&display && blt_src==&render && blt_dst_arg==&full &&
           blt_src_rect_arg==&full && blt_flags==0x55 && blt_fx_arg==fx);

    reset(); g_ui_settings_panel_open=1; g_owner_bitmap_frame_calls=1;
    assert(hook_SurfaceBlt(&display,0,&render,0,0x66,0)==41);
    assert(overlay_calls==1 && overlay_surface==&render && overlay_before_original);

    reset(); g_ui_settings_panel_open=1; g_owner_bitmap_frame_calls=1;
    assert(hook_SurfaceBlt(&display,&full,&render,&partial,0x77,fx)==41);
    assert(boundary_calls==1 && blt_calls==1 && overlay_calls==0 && draw_failed_calls==1);

    reset(); g_ui_settings_panel_open=1; g_owner_bitmap_frame_calls=1;
    assert(hook_SurfaceBlt(&render,&full,&display,&full,0x88,fx)==41);
    assert(boundary_calls==1 && overlay_calls==0);
    /* The reverse copy consumed the owner frame. The final primary copy
       must still paint the open panel, before forwarding the native call. */
    assert(hook_SurfaceBlt(&display,&full,&render,&full,0x88,fx)==41);
    assert(boundary_calls==1 && overlay_calls==1 && overlay_surface==&render);

    reset(); g_ui_settings_panel_open=1; g_owner_bitmap_frame_calls=1;
    assert(hook_SurfaceBlt(&render,&full,&render,&full,0x99,fx)==41);
    assert(boundary_calls==1 && overlay_calls==0);

    reset(); display.caps=0; display.caps_result=-1; g_ui_settings_panel_open=1; g_owner_bitmap_frame_calls=1;
    assert(hook_SurfaceBlt(&display,&full,&render,&full,0xaa,fx)==41);
    assert(boundary_calls==1 && overlay_calls==0 && draw_failed_calls==1);

    reset(); display.caps=0x200; display.caps_result=0; g_ui_settings_panel_open=1; g_owner_bitmap_frame_calls=1;
    assert(hook_SurfaceBlt(&display,&full,&small,&full,0xbb,fx)==41);
    assert(boundary_calls==1 && overlay_calls==0 && draw_failed_calls==1);

    reset(); g_ui_settings_panel_open=1; g_owner_bitmap_frame_calls=1;
    assert(hook_SurfaceBlt(&display,&full,&other,&full,0xcc,fx)==41);
    assert(boundary_calls==1 && overlay_calls==0 && draw_failed_calls==1 && !g_ui_settings_panel_open);
    puts("PASS: Blt overlay draws only from exact render-target viewport into primary; partial, reverse, self, nonprimary, nonviewport and unknown sources skip");
}
static void test_bltfast_settings_overlay(void) {
    FakeSurface display,render,small,other;
    void *display_vt[27],*render_vt[27],*small_vt[27],*other_vt[27];
    RECT full={0,0,3440,1440},partial={0,0,3000,1300};
    setup_surfaces(&display,&render,&small,&other,display_vt,render_vt,small_vt,other_vt);
    small.target=1;

    reset(); g_ui_settings_panel_open=1; g_owner_bitmap_frame_calls=1;
    assert(hook_SurfaceBltFast(&display,17,23,&render,&full,0x101)==40);
    assert(boundary_calls==1 && bltfast_calls==1 && overlay_calls==1);
    assert(overlay_surface==&render && overlay_before_original);
    assert(bltfast_self==&display && bltfast_x==17 && bltfast_y==23 &&
           bltfast_src==&render && bltfast_src_rect_arg==&full && bltfast_flags==0x101);

    reset(); g_ui_settings_panel_open=1; g_owner_bitmap_frame_calls=1;
    assert(hook_SurfaceBltFast(&display,19,29,&render,&partial,0x202)==40);
    assert(boundary_calls==1 && overlay_calls==0 && draw_failed_calls==1);

    reset(); g_ui_settings_panel_open=1; g_owner_bitmap_frame_calls=1;
    assert(hook_SurfaceBltFast(&render,31,37,&display,&full,0x303)==40);
    assert(boundary_calls==1 && overlay_calls==0);

    reset(); g_ui_settings_panel_open=1; g_owner_bitmap_frame_calls=1;
    assert(hook_SurfaceBltFast(&display,41,43,&render,&full,0x404)==40);
    assert(overlay_calls==1 && overlay_surface==&render);

    reset(); g_ui_settings_panel_open=1; g_owner_bitmap_frame_calls=1;
    assert(hook_SurfaceBltFast(&display,47,53,&small,&full,0x505)==40);
    assert(boundary_calls==0 && overlay_calls==0 && draw_failed_calls==1);
    puts("PASS: BltFast preserves x/y/source/rect/flags and skips partial, reverse and nonviewport overlay sources");
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
int main(void) {
    test_blt(); test_flip_and_empty_finalize(); test_flip_settings_overlay();
    test_blt_settings_overlay(); test_bltfast_settings_overlay(); test_end_scene();
    return 0;
}
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=Path(__file__).resolve().with_name("prm_uifix.c"))
    args = parser.parse_args()
    source = args.source.read_text()
    names = ("UIRectF", "UIGroup", "UIGroupMember", "SurfHookRec", "DevHookRec")
    types = "\n".join(extract_type(source, name) for name in names)
    for name in ("PFN_DDS7_GetSurfaceDesc", "PFN_DDS7_GetCaps",
                 "PFN_DDS7_GetAttachedSurface", "PFN_DDS7_Blt",
                 "PFN_DDS7_BltFast", "PFN_DDS7_Flip", "PFN_DDS7_Release",
                 "PFN_D3D7_EndScene"):
        match = re.search(r"^typedef[^\n]*\b" + name + r"\b[^\n]*;", source, re.M)
        if not match:
            raise ValueError(f"missing actual source typedef {name}")
        types += "\n" + match[0]
    names = ("f_abs", "rect_near", "rect_area", "rect_union", "rect_is_global", "choose_group_anchor",
             "finalize_ui_frame", "surface_dimensions", "surface_is_screenish", "blt_is_present",
             "ui_settings_surface_caps", "ui_settings_source_is_full", "ui_settings_present_source",
             "ui_settings_draw_flip", "hook_SurfaceFlip", "hook_SurfaceBlt", "hook_SurfaceBltFast",
             "hook_EndScene")
    functions = "\n".join(definition(source, name) for name in names)
    with tempfile.TemporaryDirectory(prefix="prm-present-test-") as directory:
        harness = Path(directory) / "present.c"
        binary = Path(directory) / "present-test"
        harness.write_text(PREFIX + types + STUBS + functions + TESTS)
        compiler = shlex.split(os.environ.get("CC", "clang"))
        subprocess.run(compiler + ["-m32", "-std=c11", "-O1", "-g", "-Wall", "-Wextra", "-Werror",
                                   "-fsanitize=address,undefined", "-fno-sanitize-recover=all",
                                   "-fno-omit-frame-pointer", str(harness), "-o", str(binary)], check=True)
        env = os.environ.copy()
        env.setdefault("ASAN_OPTIONS", "detect_leaks=0")
        subprocess.run([str(binary)], check=True, env=env)
    print("PASS: extracted presentation gates, surface COM protocol and in-game overlay with 32-bit ASan/UBSan fixtures")


if __name__ == "__main__":
    main()
