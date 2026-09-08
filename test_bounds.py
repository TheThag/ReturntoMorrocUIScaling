#!/usr/bin/env python3
"""Exercise the bounded-window transform through preparation, draw, and input.

This is a host harness around the production functions.  It deliberately keeps
the native lookup boundary stubbed, while using the actual persistent fit,
bitmap provenance, inverse mapping, selection, and capture code.
"""

from pathlib import Path
import os
import re
import shlex
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parent
SOURCE = (ROOT / "prm_uifix.c").read_text()


def extract_type(name):
    match = re.search(r"typedef\s+struct\s*\{[^}]*\}\s*" + re.escape(name) + r"\s*;", SOURCE)
    if not match:
        raise RuntimeError(f"missing production type {name}")
    return match[0]


def extract_function(name):
    match = re.search(r"^(?:static )?[^\n]*\b" + re.escape(name) + r"\([^;]*?\)\s*\{", SOURCE, re.M)
    if not match:
        raise RuntimeError(f"missing production function {name}")
    depth, end = 1, match.end()
    while depth:
        depth += (SOURCE[end] == "{") - (SOURCE[end] == "}")
        end += 1
    return SOURCE[match.start():end]


PREFIX = r'''
#include <assert.h>
#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
typedef uint32_t DWORD;
typedef int32_t LONG;
typedef unsigned char BYTE;
typedef uintptr_t ULONG_PTR;
typedef struct { LONG x,y; } POINT;
typedef struct { float l,t,r,b; } UIRectF;
typedef DWORD (*PFN_BitmapDraw)(void*,LONG,LONG,LONG,LONG,DWORD);
typedef union { DWORD d[4][8]; float f[4][8]; BYTE bytes[128]; } Quad;
#define MAX_OWNER_BITMAP_DRAWS 4096
#define OWNER_BITMAP_PROBES 128
#define PRM_OFFSCREEN_DP_RETURN_RVA 0x000A22A1UL
#define PRM_OFFSCREEN_DIP_RETURN_RVA 0x000A228DUL
#define WINAPI
#define CHECK(x) do { if (!(x)) { \
    fprintf(stderr,"check failed at line %d: %s\n",__LINE__,#x); exit(1); \
} } while (0)
'''


STUBS = r'''
static void owner_popup_trace_first(OwnerWindowState* st) { (void)st; }
static int owner_is_buff_tooltip(DWORD obj) { (void)obj; return 0; }
static void owner_buff_popup_offset(OwnerWindowState* st,LONG x,LONG y,LONG w) { (void)st; (void)x; (void)y; (void)w; }
static DWORD g_ui_present_serial,g_owner_input_order;
static int g_owner_submit_enabled,g_owner_scale_enabled,g_owner_tooltip_enabled;
static int g_ui_enabled,g_ui_runtime_enabled,g_ui_scale_global,g_ui_scale_unmatched;
static int g_ui_keep_on_screen;
static LONG g_ui_screen_w,g_ui_screen_h,g_ui_origin_x,g_ui_origin_y;
static int g_ui_anchor_mode,g_ui_global_threshold_percent,g_ui_scale_percent;

static OwnerWindowState g_owner_windows[32];
static DWORD g_owner_window_count;
static OwnerBitmapDrawRec g_owner_bitmap_draws[MAX_OWNER_BITMAP_DRAWS];
static OwnerBitmapScope g_owner_bitmap_scope;
static volatile LONG g_owner_bitmap_lock;
static DWORD g_owner_bitmap_calls,g_owner_bitmap_submits,g_owner_bitmap_matched;
static DWORD g_owner_bitmap_overflow,g_owner_bitmap_expired,g_owner_bitmap_mismatched;
static DWORD g_owner_bitmap_unsupported,g_owner_bitmap_peak,g_owner_bitmap_offscreen;
static DWORD g_owner_bitmap_unowned,g_owner_bitmap_order,g_owner_bitmap_active_count,g_owner_bitmap_frame_calls;
static DWORD g_owner_tagged_draws,g_ui_scaled_draws;
static int g_owner_bitmap_hooks_installed;

static OwnerInputRegion g_owner_input_regions[32];
static OwnerHitSelection g_owner_hit_selection;
static int owner_input_select_region(const POINT*,OwnerInputRegion*,DWORD*);
static DWORD g_transient_tooltip_object;
static int owner_is_transient_tooltip(DWORD object) {
    return object==g_transient_tooltip_object;
}
static OwnerCaptureLink g_owner_capture_links[32];
static DWORD g_owner_input_region_count,g_owner_capture_link_count;
static DWORD g_owner_capture_object,g_owner_capture_root;
static float g_owner_capture_ax,g_owner_capture_ay;
static float g_owner_capture_scale,g_owner_capture_offset_x,g_owner_capture_offset_y;
static int g_owner_capture_native_size;
static DWORD g_owner_capture_maps,g_owner_capture_changes,g_owner_capture_unknown;
static DWORD g_owner_mapped_mouse,g_owner_input_candidates,g_owner_input_overlap_hits;
static int g_owner_input_remap_enabled,g_input_enabled,g_input_runtime_enabled;
static int g_fake_capture,g_locked;
static DWORD g_owner_trace_calls;
static const void* g_unreadable;
static DWORD g_draw_object;
static Quad g_draw_quad;

static DWORD current_thread(void) { return 17; }
static DWORD (*g_GetCurrentThreadId)(void)=current_thread;
static int mem_readable(const void* p,DWORD n) {
    return p && p!=g_unreadable && n<=128;
}
static int s_contains(const char* s,const char* needle) {
    return s && needle && strstr(s,needle)!=0;
}
static int s_equal(const char* a,const char* b) {
    return a && b && strcmp(a,b)==0;
}
static void owner_input_region_lock(void) { assert(!g_locked); g_locked=1; }
static void owner_input_region_unlock(void) { assert(g_locked); g_locked=0; }
static DWORD owner_native_capture(void) { return (DWORD)g_fake_capture; }
static OwnerWindowState* owner_state_for(DWORD object,int create) {
    OwnerWindowState* st;
    if(!object || object>=32) return 0;
    st=&g_owner_windows[object];
    if(!st->object_ptr && create) {
        st->object_ptr=object;
        st->vtable_ptr=object*0x1000UL;
        strcpy(st->class_name,"UIItemWnd");
        ++g_owner_window_count;
    }
    return st->object_ptr?st:0;
}
static int owner_fit_connected(OwnerWindowState* st) {
    (void)st; /* Basic/Menu native-controller linkage belongs to the native fixture. */
    return 0;
}
static int cursor_consume_vertices(DWORD fvf,const void* verts,DWORD nverts) {
    (void)fvf; (void)verts; (void)nverts; return 0;
}
static void vtrace_note_d3d_ui(void) { ++g_owner_trace_calls; }
static int owner_submit_match_rect(const UIRectF* r,DWORD* object) {
    (void)r; if(object) *object=0; return 0;
}
static void owner_collect_rect(DWORD object,const UIRectF* r) {
    (void)object; (void)r;
}
static int owner_get_transform(DWORD object,float* ax,float* ay) {
    (void)object; if(ax) *ax=0; if(ay) *ay=0; return 0;
}
static void collect_ui_rect(float l,float t,float r,float b) {
    (void)l; (void)t; (void)r; (void)b;
}
static int get_group_transform_for_rect(const UIRectF* r,float* ax,float* ay) {
    (void)r; (void)ax; (void)ay; return 0;
}
'''


PRODUCTION = "\n".join(extract_function(name) for name in (
    "fvf_stride", "ui_scale_factor", "f_abs", "rect_contains_point", "rect_area",
    "rect_is_global", "choose_group_anchor", "owner_class_is_hover_popup",
    "owner_class_is_world_label", "owner_class_is_world_title", "owner_class_is_world_name",
    "owner_class_should_hook", "owner_input_touch_state", "owner_fit_rect", "owner_popup_offset",
    "owner_bitmap_prepare", "owner_bitmap_draw_c", "owner_bitmap_registry_lock",
    "owner_bitmap_registry_unlock", "owner_bitmap_bucket", "owner_bitmap_forget",
    "owner_bitmap_note_vertices", "owner_bitmap_consume_transform",
    "owner_input_region_bounds", "owner_input_map_region", "owner_input_map_capture",
    "owner_input_select_region", "remap_owner_point_selected", "remap_owner_point",
    "looks_like_ui_vertices", "make_scaled_ui_vertices",
))


TESTS = r'''
static void reset_all(void) {
    memset(&g_owner_hit_selection,0,sizeof(g_owner_hit_selection));
    g_transient_tooltip_object=1;
    memset(g_owner_windows,0,sizeof(g_owner_windows));
    memset(g_owner_bitmap_draws,0,sizeof(g_owner_bitmap_draws));
    memset(&g_owner_bitmap_scope,0,sizeof(g_owner_bitmap_scope));
    memset(g_owner_input_regions,0,sizeof(g_owner_input_regions));
    memset(g_owner_capture_links,0,sizeof(g_owner_capture_links));
    g_owner_window_count=0; g_owner_bitmap_lock=0;
    g_owner_bitmap_calls=g_owner_bitmap_submits=g_owner_bitmap_matched=0;
    g_owner_bitmap_overflow=g_owner_bitmap_expired=g_owner_bitmap_mismatched=0;
    g_owner_bitmap_unsupported=g_owner_bitmap_peak=g_owner_bitmap_offscreen=0;
    g_owner_bitmap_unowned=g_owner_bitmap_order=g_owner_bitmap_active_count=g_owner_bitmap_frame_calls=0;
    g_owner_tagged_draws=g_ui_scaled_draws=g_owner_trace_calls=0;
    g_owner_bitmap_hooks_installed=1;
    g_owner_input_region_count=g_owner_capture_link_count=0;
    g_owner_capture_object=g_owner_capture_root=0;
    g_owner_capture_ax=g_owner_capture_ay=0;
    g_owner_capture_scale=0; g_owner_capture_offset_x=g_owner_capture_offset_y=0;
    g_owner_capture_native_size=0;
    g_owner_capture_maps=g_owner_capture_changes=g_owner_capture_unknown=0;
    g_owner_mapped_mouse=g_owner_input_candidates=g_owner_input_overlap_hits=0;
    g_owner_input_remap_enabled=g_input_enabled=g_input_runtime_enabled=1;
    g_fake_capture=0; g_unreadable=0;
    g_ui_present_serial=100; g_owner_input_order=0;
    g_ui_screen_w=1920; g_ui_screen_h=1080; g_ui_origin_x=g_ui_origin_y=0;
    g_ui_anchor_mode=1; g_ui_global_threshold_percent=95;
    g_ui_scale_percent=200; g_ui_keep_on_screen=1;
    g_ui_enabled=g_ui_runtime_enabled=1; g_ui_scale_global=1; g_ui_scale_unmatched=0;
    g_owner_submit_enabled=g_owner_scale_enabled=g_owner_tooltip_enabled=1;
    g_GetCurrentThreadId=current_thread;
}

static OwnerWindowState* window(DWORD object,const char* class_name) {
    OwnerWindowState* st=owner_state_for(object,1);
    CHECK(st);
    if(class_name) { memset(st->class_name,0,sizeof(st->class_name)); strncpy(st->class_name,class_name,sizeof(st->class_name)-1); }
    return st;
}
static void quad(Quad* q,float x,float y,float w,float h) {
    DWORD i; memset(q,0,sizeof(*q));
    for(i=0;i<4;++i) {
        q->f[i][0]=x+((i&1)?w:0); q->f[i][1]=y+((i&2)?h:0);
        q->f[i][2]=0.0f; q->f[i][3]=1.0f;
        q->d[i][4]=0xffffffffUL; q->d[i][5]=0xff000000UL;
        q->f[i][6]=(i&1)?1.0f:0.0f; q->f[i][7]=(i&2)?1.0f:0.0f;
    }
}
static void publish_region(unsigned int index,OwnerWindowState* st,int native_size) {
    OwnerInputRegion* r=&g_owner_input_regions[index];
    memset(r,0,sizeof(*r));
    r->rect=st->input_local_bbox;
    r->rect.l+=(float)st->pos_x; r->rect.r+=(float)st->pos_x;
    r->rect.t+=(float)st->pos_y; r->rect.b+=(float)st->pos_y;
    r->ax=st->ax; r->ay=st->ay; r->fit_scale=st->fit_scale;
    r->offset_x=st->offset_x; r->offset_y=st->offset_y;
    r->object_ptr=st->object_ptr; r->present=g_ui_present_serial;
    r->input_order=st->last_input_order; r->exact_order=st->last_draw_order;
    r->vtable_ptr=st->vtable_ptr; r->native_size=native_size;
    if(g_owner_input_region_count<=index) g_owner_input_region_count=index+1;
}
static void assert_close(float a,float b,float epsilon) { CHECK(fabsf(a-b)<=epsilon); }
static void assert_inside(const UIRectF* r) {
    assert_close(r->l, fmaxf(0.0f,r->l), 0.01f);
    assert_close(r->t, fmaxf(0.0f,r->t), 0.01f);
    CHECK(r->r <= (float)g_ui_screen_w+0.01f);
    CHECK(r->b <= (float)g_ui_screen_h+0.01f);
    CHECK(r->r>=r->l && r->b>=r->t);
}
static void assert_scaled_quad(const Quad* in,const Quad* out,const OwnerBitmapScope* scope) {
    DWORD i,j; float s=scope->fit_scale;
    for(i=0;i<4;++i) {
        float x=scope->ax+(in->f[i][0]-scope->ax)*s+scope->offset_x;
        float y=scope->ay+(in->f[i][1]-scope->ay)*s+scope->offset_y;
        assert_close(out->f[i][0],x,0.001f); assert_close(out->f[i][1],y,0.001f);
        for(j=2;j<8;++j) CHECK(out->d[i][j]==in->d[i][j]);
    }
}

static void test_edges_corners_scales(void) {
    const int scales[]={125,133,150,175,200};
    const LONG screens[][2]={{1280,720},{1920,1080},{2560,1440},{3440,1440}};
    unsigned int si,ri,corner; const LONG* screen;
    for(si=0;si<sizeof(scales)/sizeof(scales[0]);++si) for(ri=0;ri<sizeof(screens)/sizeof(screens[0]);++ri) {
        LONG w=(LONG)((float)screens[ri][0]*0.70f),h=(LONG)((float)screens[ri][1]*0.60f);
        reset_all(); g_ui_scale_percent=scales[si]; g_ui_screen_w=screens[ri][0]; g_ui_screen_h=screens[ri][1];
        screen=screens[ri];
        for(corner=0;corner<4;++corner) {
            LONG x=(corner&1)?screen[0]-w:0, y=(corner&2)?screen[1]-h:0;
            OwnerWindowState* st=window(1+corner,"UIItemWnd"); UIRectF src,dst; OwnerInputRegion r; POINT p;
            CHECK(owner_bitmap_prepare(st->object_ptr,x,y,w,h));
            src=(UIRectF){(float)x,(float)y,(float)(x+w),(float)(y+h)};
            memset(&r,0,sizeof(r)); r.rect=src; r.ax=st->ax; r.ay=st->ay;
            r.fit_scale=st->fit_scale; r.offset_x=st->offset_x; r.offset_y=st->offset_y;
            owner_input_region_bounds(&r,&dst); assert_inside(&dst);
            CHECK(st->fit_scale>0.0f && st->fit_scale<=(float)scales[si]*0.01f+0.001f);
            p.x=(LONG)((dst.l+dst.r)*0.5f+0.5f); p.y=(LONG)((dst.t+dst.b)*0.5f+0.5f);
            CHECK(owner_input_map_region(&p,&r));
            CHECK(labs(p.x-(x+w/2))<=1 && labs(p.y-(y+h/2))<=1);
            publish_region(corner,st,0);
        }
    }
    puts("PASS bounds: 4 corners stay inside at 125/133/150/175/200% across 720/1080/1440-high screens and inverse centers round-trip");
}

static void test_persistent_edge_offset(void) {
    OwnerWindowState* st; OwnerInputRegion r; UIRectF b; float retained; POINT p;
    LONG old_pos;
    reset_all(); g_ui_screen_w=3440; g_ui_screen_h=1440; g_ui_scale_percent=200;
    st=window(1,"UIItemWnd");
    CHECK(owner_bitmap_prepare(1,3000,100,500,400));
    old_pos=st->pos_x; retained=st->offset_x;
    CHECK(owner_bitmap_prepare(1,100,100,500,400));
    CHECK(st->pos_x==100 && old_pos==3000);
    retained=st->offset_x; CHECK(retained>3000.0f);
    r=(OwnerInputRegion){0}; r.rect=(UIRectF){100,100,600,500}; r.ax=st->ax; r.ay=st->ay;
    r.fit_scale=st->fit_scale; r.offset_x=st->offset_x; r.offset_y=st->offset_y;
    owner_input_region_bounds(&r,&b); assert_inside(&b); assert_close(b.l,0.0f,0.01f);
    CHECK(owner_bitmap_prepare(1,100,100,500,400)); CHECK(st->offset_x==retained);
    CHECK(owner_bitmap_prepare(1,105,100,500,400));
    r.rect=(UIRectF){105,100,605,500}; r.offset_x=st->offset_x; r.offset_y=st->offset_y;
    owner_input_region_bounds(&r,&b); CHECK(b.l>0.0f && b.l<20.0f); CHECK(st->offset_x==retained);
    p.x=(LONG)((b.l+b.r)*0.5f+0.5f); p.y=(LONG)((b.t+b.b)*0.5f+0.5f);
    CHECK(owner_input_map_region(&p,&r)); CHECK(labs(p.x-355)<=1 && labs(p.y-300)<=1);
    puts("PASS bounds: persistent correction survives repeated edge frames and lets an inward native drag move away from the edge");
}

static DWORD original_draw(void* dc,LONG x,LONG y,LONG w,LONG h,DWORD color) {
    (void)dc; (void)x; (void)y; (void)w; (void)h; (void)color;
    owner_bitmap_note_vertices(&g_draw_quad,4,&g_owner_bitmap_scope);
    return 0x55UL;
}
static void test_queue_draw_and_capture_freeze(void) {
    OwnerWindowState* st; OwnerBitmapScope saved,before_draw; Quad a,b,out,scratch; POINT p;
    OwnerInputRegion r; UIRectF bounds;
    reset_all(); g_ui_screen_w=3440; g_ui_screen_h=1440; g_ui_scale_percent=175;
    st=window(1,"UIItemWnd");
    CHECK(owner_bitmap_prepare(1,100,100,300,200)); saved=g_owner_bitmap_scope;
    quad(&a,100,100,150,100); quad(&b,250,100,150,100);
    owner_bitmap_note_vertices(&a,4,&saved); owner_bitmap_note_vertices(&b,4,&saved);
    /* A settings-panel scale change cannot rewrite already queued tile records. */
    g_ui_scale_percent=200; CHECK(owner_bitmap_prepare(1,400,200,300,200));
    CHECK(make_scaled_ui_vertices(5,0x1c4,&a,4,scratch.bytes,sizeof(scratch),0,0)==&scratch);
    CHECK(make_scaled_ui_vertices(5,0x1c4,&b,4,out.bytes,sizeof(out),0,0)==&out);
    assert_scaled_quad(&a,&scratch,&saved); assert_scaled_quad(&b,&out,&saved);
    CHECK(g_owner_bitmap_active_count==0 && g_owner_bitmap_matched==2);
    /* The actual bitmap wrapper brackets the original draw and restores scope. */
    g_ui_scale_percent=150; g_draw_quad=a; g_draw_object=1; before_draw=g_owner_bitmap_scope;
    CHECK(owner_bitmap_draw_c(1,0,original_draw,100,100,300,200,0xffffffffUL)==0x55UL);
    CHECK(g_owner_bitmap_scope.object_ptr==before_draw.object_ptr &&
          g_owner_bitmap_scope.fit_scale==before_draw.fit_scale &&
          g_owner_bitmap_scope.offset_x==before_draw.offset_x &&
          g_owner_bitmap_active_count==1);
    CHECK(make_scaled_ui_vertices(5,0x1c4,&g_draw_quad,4,out.bytes,sizeof(out),0,0)==&out);
    CHECK(g_owner_bitmap_active_count==0);
    /* Publish the saved transform as input, then freeze it across a later change. */
    memset(&r,0,sizeof(r)); r.rect=(UIRectF){100,100,400,300}; r.ax=saved.ax; r.ay=saved.ay;
    r.fit_scale=saved.fit_scale; r.offset_x=saved.offset_x; r.offset_y=saved.offset_y;
    r.object_ptr=1; r.vtable_ptr=st->vtable_ptr; r.present=g_ui_present_serial; r.input_order=1;
    g_owner_input_regions[0]=r; g_owner_input_region_count=1;
    owner_input_region_bounds(&r,&bounds); p.x=(LONG)((bounds.l+bounds.r)*0.5f+0.5f); p.y=(LONG)((bounds.t+bounds.b)*0.5f+0.5f);
    g_fake_capture=1; CHECK(owner_input_map_capture(&p,1)); CHECK(labs(p.x-250)<=1 && labs(p.y-200)<=1);
    g_ui_scale_percent=125; g_owner_input_regions[0].fit_scale=1.0f; g_owner_input_regions[0].offset_x=0; g_owner_input_regions[0].offset_y=0;
    p.x=(LONG)((bounds.l+bounds.r)*0.5f+0.5f); p.y=(LONG)((bounds.t+bounds.b)*0.5f+0.5f);
    CHECK(owner_input_map_capture(&p,1)); CHECK(labs(p.x-250)<=1 && labs(p.y-200)<=1);
    puts("PASS queue/draw/input: deferred tiles retain fit scale and offsets, draw scope restores, and capture inverse freezes the published transform");
}

static void test_oversized_toggles_and_exclusions(void) {
    OwnerWindowState *st,*world,*title,*name; OwnerInputRegion r; UIRectF b; Quad q,out;
    reset_all(); g_ui_screen_w=1920; g_ui_screen_h=1080; g_ui_scale_percent=200;
    /* Uniform fit handles a window larger than the viewport while retaining its center. */
    st=window(1,"UIUnknownWnd"); CHECK(owner_class_should_hook(st->class_name));
    CHECK(owner_bitmap_prepare(1,0,0,1800,1000));
    r=(OwnerInputRegion){0}; r.rect=(UIRectF){0,0,1800,1000}; r.ax=st->ax; r.ay=st->ay;
    r.fit_scale=st->fit_scale; r.offset_x=st->offset_x; r.offset_y=st->offset_y;
    owner_input_region_bounds(&r,&b); assert_inside(&b); CHECK(b.r-b.l<=1920.01f && b.b-b.t<=1080.01f);
    quad(&q,0,0,1800,1000); owner_bitmap_note_vertices(&q,4,&g_owner_bitmap_scope);
    CHECK(make_scaled_ui_vertices(5,0x1c4,&q,4,out.bytes,sizeof(out),0,0)==&out);
    CHECK(g_owner_bitmap_active_count==0);
    /* KeepOnScreen=0 is an explicit opt-out and therefore may leave the native rect clipped. */
    g_ui_keep_on_screen=0; CHECK(owner_bitmap_prepare(2,1700,900,300,200)); CHECK(window(2,0)->offset_x==0 && window(2,0)->offset_y==0);
    r=(OwnerInputRegion){0}; r.rect=(UIRectF){1700,900,2000,1100}; r.ax=window(2,0)->ax; r.ay=window(2,0)->ay; r.fit_scale=window(2,0)->fit_scale;
    owner_input_region_bounds(&r,&b); CHECK(b.r>1920.0f || b.b>1080.0f);
    g_ui_keep_on_screen=1; g_ui_runtime_enabled=0; CHECK(owner_bitmap_prepare(2,1700,900,300,200)); CHECK(window(2,0)->offset_x==0 && window(2,0)->offset_y==0);
    g_ui_runtime_enabled=1;
    /* Native-size global windows keep native coordinates and bypass the scaler. */
    g_ui_scale_global=0; st=window(3,"UIItemWnd"); CHECK(owner_bitmap_prepare(3,0,0,1920,1080));
    CHECK(g_owner_bitmap_scope.native_size && st->fit_scale==2.0f && st->offset_x==0.0f);
    quad(&q,100,100,100,100); owner_bitmap_note_vertices(&q,4,&g_owner_bitmap_scope);
    CHECK(make_scaled_ui_vertices(5,0x1c4,&q,4,out.bytes,sizeof(out),0,0)==&q);
    CHECK(!st->last_input_order);
    /* World-attached records deliberately preserve their native attachment point. */
    g_ui_scale_global=1; world=window(4,"CSignBoardWnd");
    CHECK(owner_bitmap_prepare(4,1700,900,201,101)); CHECK(world->ax==1800 && world->ay==950);
    CHECK(world->offset_x==0 && world->offset_y==0 && world->last_input_order==0);
    title=window(5,"UIChatRoomTitle"); CHECK(owner_bitmap_prepare(5,500,400,140,34));
    CHECK(title->ax==570 && title->ay==434 && title->offset_x==0 && title->offset_y==0 && title->last_input_order);
    name=window(6,"UINameBalloonText"); CHECK(owner_bitmap_prepare(6,500,400,140,34));
    CHECK(name->ax==570 && name->ay==417 && name->offset_x==0 && name->offset_y==0 && name->last_input_order==0);
    puts("PASS exclusions: oversized fit, KeepOnScreen/runtime toggles, native full-screen bypass, and world/title/name attachment policies remain distinct");
}

static void test_independent_roots(void) {
    OwnerWindowState *first,*second; OwnerInputRegion r; POINT p; UIRectF b;
    reset_all(); g_ui_screen_w=3440; g_ui_screen_h=1440; g_ui_scale_percent=200;
    first=window(10,"UIArbitraryFirstWnd"); second=window(11,"UIArbitrarySecondWnd");
    CHECK(owner_bitmap_prepare(10,3000,1000,500,300));
    CHECK(owner_bitmap_prepare(11,-100,1000,500,300));
    CHECK(first->object_ptr==10 && second->object_ptr==11 && first->vtable_ptr!=second->vtable_ptr);
    CHECK(first->offset_x<0.0f && second->offset_x>0.0f);
    r=(OwnerInputRegion){0}; r.rect=(UIRectF){3000,1000,3500,1300}; r.ax=first->ax; r.ay=first->ay;
    r.fit_scale=first->fit_scale; r.offset_x=first->offset_x; r.offset_y=first->offset_y;
    owner_input_region_bounds(&r,&b); p.x=(LONG)((b.l+b.r)*0.5f+0.5f); p.y=(LONG)((b.t+b.b)*0.5f+0.5f);
    CHECK(owner_input_map_region(&p,&r)); CHECK(labs(p.x-3250)<=1 && labs(p.y-1150)<=1);
    publish_region(0,first,0); publish_region(1,second,0);
    p.x=(LONG)((b.l+b.r)*0.5f+0.5f); p.y=(LONG)((b.t+b.b)*0.5f+0.5f);
    CHECK(remap_owner_point(&p)); CHECK(labs(p.x-3250)<=1 && labs(p.y-1150)<=1);
    CHECK(first->pos_x==3000 && second->pos_x==-100);
    puts("PASS roots: Unrelated windows keep separate persistent offsets, positions, anchors, and inverse input mappings");
}

static void test_first_hover_popup(void) {
    const char* classes[]={"UITransBalloonText","UICharInfoBalloonText","UIToolTipWnd"};
    int c,visit; OwnerWindowState* st; OwnerBitmapScope scope; Quad q,out;
    for(c=0;c<3;++c) {
        reset_all(); g_ui_screen_w=1920; g_ui_screen_h=1080; g_ui_scale_percent=200;
        CHECK(owner_class_should_hook(classes[c]));
        CHECK(owner_class_is_hover_popup(classes[c]));
        st=window(1,classes[c]);
        for(visit=0;visit<3;++visit) {
            LONG x=visit==1?1800:400+visit*100,y=visit==1?1000:300;
            /* No previous frame, group match, or warm-up is available. Reuse
               the same popup after another control changed its position. */
            CHECK(owner_bitmap_prepare(1,x,y,180,40)); scope=g_owner_bitmap_scope;
            CHECK(scope.object_ptr==1 && scope.ax==x && scope.ay==y);
            CHECK(!st->last_input_order);
            quad(&q,x,y,180,40); owner_bitmap_note_vertices(&q,4,&scope);
            CHECK(make_scaled_ui_vertices(5,0x1c4,&q,4,out.bytes,sizeof(out),0,0)==&out);
            assert_scaled_quad(&q,&out,&scope);
            assert_close(out.f[1][0]-out.f[0][0],360.0f,0.01f);
            CHECK(out.f[0][0]>=0 && out.f[1][0]<=1920);
            CHECK(out.f[0][1]>=0 && out.f[2][1]<=1080);
            if(visit!=1) CHECK(scope.offset_x==0 && scope.offset_y==0);
            ++g_ui_present_serial;
        }
    }
    CHECK(!owner_class_should_hook("UIBalloonText"));
    CHECK(!owner_class_should_hook("UIUnknownBalloonText"));
    st=window(3,"UICharInfoBalloonText");
    CHECK(owner_bitmap_prepare(3,-400,-400,140,200));
    CHECK(g_owner_bitmap_scope.native_size && st->offset_x==0 && st->offset_y==0);
    reset_all(); g_ui_screen_w=1920; g_ui_screen_h=1080; g_ui_scale_percent=200;
    g_owner_input_region_count=1;
    g_owner_input_regions[0]=(OwnerInputRegion){0};
    g_owner_input_regions[0].object_ptr=10; g_owner_input_regions[0].vtable_ptr=0x10000;
    g_owner_input_regions[0].rect=(UIRectF){100,100,400,300};
    g_owner_input_regions[0].fit_scale=2; g_owner_input_regions[0].present=g_ui_present_serial;
    g_owner_hit_selection.valid=1; g_owner_hit_selection.raw=(POINT){250,250};
    g_owner_hit_selection.region=g_owner_input_regions[0];
    st=window(1,"UITransBalloonText");
    CHECK(owner_bitmap_prepare(1,120,80,180,40)); scope=g_owner_bitmap_scope;
    quad(&q,120,80,180,40); owner_bitmap_note_vertices(&q,4,&scope);
    CHECK(make_scaled_ui_vertices(5,0x1c4,&q,4,out.bytes,sizeof(out),0,0)==&out);
    assert_close(out.f[0][0],240,0.01f); assert_close(out.f[0][1],160,0.01f);
    assert_close(out.f[1][0]-out.f[0][0],360,0.01f);
    /* The same RTTI class is also native actor speech. A hovered control must
       never translate that other instance or clamp it away from its actor. */
    st=window(2,"UITransBalloonText");
    CHECK(owner_bitmap_prepare(2,700,500,140,30)); scope=g_owner_bitmap_scope;
    CHECK(scope.ax==770 && scope.ay==530 && scope.offset_x==0 && scope.offset_y==0);
    CHECK(!st->last_input_order);
    quad(&q,700,500,140,30); owner_bitmap_note_vertices(&q,4,&scope);
    CHECK(make_scaled_ui_vertices(5,0x1c4,&q,4,out.bytes,sizeof(out),0,0)==&out);
    assert_close((out.f[0][0]+out.f[1][0])*0.5f,770,0.01f);
    assert_close(out.f[2][1],530,0.01f);
    puts("PASS popups: exact transient/character-info classes scale on first draw and revisit, fit at edges, and never claim input");
}

static void test_moving_player_gauge(void) {
    int i; OwnerWindowState* st; OwnerBitmapScope scope; Quad q,out;
    reset_all(); g_ui_screen_w=3440; g_ui_screen_h=1440; g_ui_scale_percent=200;
    CHECK(owner_class_should_hook("UIPlayerGage"));
    st=window(1,"UIPlayerGage");
    for(i=0;i<10;++i) {
        LONG x=900+i*37,y=800-i*19;
        CHECK(owner_bitmap_prepare(1,x,y,60,9)); scope=g_owner_bitmap_scope;
        CHECK(scope.ax==x+30 && scope.ay==y+4);
        CHECK(scope.offset_x==0 && scope.offset_y==0 && !st->last_input_order);
        quad(&q,x,y,60,9); owner_bitmap_note_vertices(&q,4,&scope);
        CHECK(make_scaled_ui_vertices(5,0x1c4,&q,4,out.bytes,sizeof(out),0,0)==&out);
        assert_scaled_quad(&q,&out,&scope);
        assert_close((out.f[0][0]+out.f[1][0])*0.5f,(float)(x+30),0.01f);
        /* Center follows the native integer anchor, even with odd height. */
        assert_close(out.f[0][1],(float)(y-4),0.01f);
        ++g_ui_present_serial;
    }
    CHECK(!owner_class_is_world_label("UIBarGraphPlayer"));
    puts("PASS player gauge: each movement updates the exact world-window anchor, preserves bar alignment, and excludes HUD graph controls");
}

int main(void) {
    test_edges_corners_scales();
    test_persistent_edge_offset();
    test_queue_draw_and_capture_freeze();
    test_oversized_toggles_and_exclusions();
    test_independent_roots();
    test_first_hover_popup();
    test_moving_player_gauge();
    return 0;
}
'''


def main():
    types = "\n".join(extract_type(name) for name in (
        "OwnerWindowState", "OwnerBitmapDrawRec", "OwnerBitmapScope", "OwnerInputRegion",
        "OwnerCaptureLink", "OwnerHitSelection"))
    code = PREFIX + types + STUBS + PRODUCTION + TESTS
    with tempfile.TemporaryDirectory(prefix="prm-bounds-test-") as directory:
        c_file = Path(directory) / "bounds.c"
        binary = Path(directory) / "bounds-test"
        c_file.write_text(code)
        compiler = shlex.split(os.environ.get("CC", "clang"))
        flags = ["-std=c11", "-O1", "-g", "-Wall", "-Wextra", "-Werror",
                 "-Wno-unused-variable", "-Wno-unused-parameter", "-fsanitize=address,undefined",
                 "-fno-omit-frame-pointer", str(c_file), "-o", str(binary)]
        subprocess.run(compiler + flags, check=True)
        env = os.environ.copy()
        env.setdefault("ASAN_OPTIONS", "detect_leaks=0")
        subprocess.run([str(binary)], check=True, env=env)
    print("PASS: bounded-window production transform harness")


if __name__ == "__main__":
    main()
