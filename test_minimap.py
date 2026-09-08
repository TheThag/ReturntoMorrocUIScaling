#!/usr/bin/env python3
"""Exercise the production minimap owner wrapper and bitmap provenance path.

The minimap wrapper, owner preparation, queue provenance, and final vertex
transform are extracted from prm_uifix.c.  The synthetic 32-bit fixture keeps
the native scene argument distinct from the UIMinimapZoomWnd object looked up
through the production RVA.  ASan/UBSan cover the complete scoped draw path;
native lookup and renderer APIs are represented by explicit fixture memory and
callbacks.
"""

from pathlib import Path
import os
import subprocess
import tempfile

import test_bitmap as bitmap


ROOT = Path(__file__).resolve().parent
source = (ROOT / "prm_uifix.c").read_text()


def function(name):
    return bitmap.function(name)


def constant(name):
    return bitmap.constant(name)


# Keep the same owner registry/state extraction used by test_bitmap.py, then
# add the minimap lookup slot required by the scoped wrapper.
types = bitmap.struct_type("OwnerWindowState") + "\n" + source[
    source.index("static int g_owner_bitmap_enabled="):
    source.index("#define MAX_OWNER_CAPTURE_LINKS")
]
types += "\n" + "\n".join(constant(name) for name in (
    "OWNER_BITMAP_PROBES", "PRM_MAP_VTABLE_RVA", "PRM_OFFSCREEN_DP_RETURN_RVA",
    "PRM_OFFSCREEN_DIP_RETURN_RVA", "PRM_MINIMAP_WINDOW_RVA",
))

prefix = bitmap.prefix.replace(
    "static DWORD thread_id(void) { return 17; }",
    "static DWORD current_thread=17;\n"
    "static DWORD thread_id(void) { return current_thread; }",
).replace(
    "typedef DWORD (*PFN_BitmapDraw)",
    "typedef DWORD (__attribute__((thiscall)) *PFN_BitmapDraw)",
).replace("#define WINAPI\n", "#define WINAPI __attribute__((stdcall))\n")
prefix += r"""
typedef void* HMODULE;
static HMODULE g_exe;
static DWORD g_exe_size;
typedef DWORD (__attribute__((thiscall)) *PFN_WindowOverlayDraw)(void*);
typedef void (__attribute__((thiscall)) *PFN_SpriteSubmit)(void*,void*,DWORD);
static PFN_WindowOverlayDraw g_owner_minimap_draw;
static PFN_SpriteSubmit g_owner_bitmap_submit;

/* Native UIWindow layout used by owner_minimap_draw_scoped. */
typedef struct {
    BYTE bytes[0x14];
    LONG w,h,x,y;
} NativeWindow;
typedef struct { void* verts; DWORD count; } Primitive;
typedef union { DWORD d[4][8]; float f[4][8]; BYTE bytes[128]; } Quad;
static NativeWindow minimap_window,wrong_window,unreadable_window,scene;
static BYTE* exe_fixture;
"""

stubs = bitmap.stubs.replace(
    "static OwnerWindowState* owner_state_for(",
    "static OwnerWindowState* fixture_state_for(",
)
stubs += r"""
static OwnerWindowState* window_state(DWORD obj,int index,int create) {
    OwnerWindowState* st=&states[index];
    if(!st->object_ptr && create) {
        st->object_ptr=obj;
        st->vtable_ptr=0x10000000UL+(DWORD)index*0x1000UL;
    }
    return st->object_ptr?st:0;
}
static OwnerWindowState* owner_state_for(DWORD obj,int create) {
    if(obj==(DWORD)(ULONG_PTR)&minimap_window) return window_state(obj,1,create);
    if(obj==(DWORD)(ULONG_PTR)&wrong_window) return window_state(obj,2,create);
    if(obj==(DWORD)(ULONG_PTR)&unreadable_window) return window_state(obj,3,create);
    return fixture_state_for(obj,create);
}
"""

production = bitmap.production + "\n" + "\n".join(function(name) for name in (
    "owner_bitmap_queue_scoped", "owner_minimap_draw_scoped",
))

tests = r"""
#define MINIMAP_X (3440-145)
#define MINIMAP_Y 17
#define MINIMAP_W 128
#define MINIMAP_H 140

static Quad direct_quads[4],manager_quad;
static Primitive direct_primitives[4],manager_primitive;
static DWORD renderer,manager_dc;
static DWORD expected_flags;
static void* expected_renderer;
static Primitive* expected_primitive;
static DWORD scene_calls,manager_calls,queue_calls;
static int expect_valid;
static OwnerBitmapScope direct_scope,manager_scope;

static void set_window(NativeWindow* w,LONG x,LONG y,LONG width,LONG height) {
    memset(w,0,sizeof(*w)); w->w=width; w->h=height; w->x=x; w->y=y;
}
static void set_lookup(void* owner) {
    *(DWORD*)(exe_fixture+PRM_MINIMAP_WINDOW_RVA)=(DWORD)(ULONG_PTR)owner;
}
static void outer_scope(OwnerBitmapScope* out) {
    memset(out,0,sizeof(*out));
    out->object_ptr=0x10203040UL; out->vtable_ptr=0x50607080UL;
    out->thread=17; out->ax=31.25f; out->ay=47.5f; out->native_size=1;
}

static void quad_depth(Quad* q,float x,float y,float w,float h,float z,float rhw) {
    DWORD i; memset(q,0,sizeof(*q));
    for(i=0;i<4;++i) {
        q->f[i][0]=x+((i&1)?w:0); q->f[i][1]=y+((i&2)?h:0);
        q->f[i][2]=z; q->f[i][3]=rhw;
        q->d[i][4]=0xffffffffUL; q->d[i][5]=0xff000000UL;
        q->f[i][6]=(i&1)?1.0f:0.0f; q->f[i][7]=(i&2)?1.0f:0.0f;
    }
}
static void marker_quad(Quad* q,float x,float y) {
    DWORD i;
    quad_depth(q,x,y,12,10,0.8f,0.1f);
    /* The direction marker is a degenerate triangle-like four-vertex draw. */
    q->f[0][0]=x;    q->f[0][1]=y;
    q->f[1][0]=x+12; q->f[1][1]=y;
    q->f[2][0]=x+6;  q->f[2][1]=y+10;
    q->f[3][0]=x+6;  q->f[3][1]=y+10;
    for(i=0;i<4;++i) { q->f[i][2]=0.8f; q->f[i][3]=0.1f; }
}
static void submit(Primitive* p,DWORD flags) {
    expected_renderer=&renderer; expected_primitive=p; expected_flags=flags;
    owner_bitmap_queue_scoped(expected_renderer,p,flags);
}

static void __attribute__((thiscall)) native_queue(void* self,void* primitive,DWORD flags) {
    CHECK(self==expected_renderer && primitive==expected_primitive && flags==expected_flags);
    ++queue_calls;
}
static DWORD __attribute__((thiscall)) native_minimap(void* actual_scene) {
    unsigned int i;
    CHECK(actual_scene==&scene && actual_scene!=(void*)&minimap_window);
    ++scene_calls;
    if(expect_valid) {
        CHECK(g_owner_bitmap_scope.object_ptr==(DWORD)(ULONG_PTR)&minimap_window);
        CHECK(g_owner_bitmap_scope.thread==17);
        direct_scope=g_owner_bitmap_scope;
    } else {
        /* The wrapper must clear the inherited object/thread before forwarding. */
        CHECK(!g_owner_bitmap_scope.object_ptr && !g_owner_bitmap_scope.thread);
    }
    for(i=0;i<4;++i) submit(&direct_primitives[i],0x201+i);
    return 0x13579bdfUL;
}
static DWORD __attribute__((thiscall)) native_manager_bitmap(
    void* dc,LONG x,LONG y,LONG w,LONG h,DWORD color) {
    CHECK(dc==(void*)&manager_dc && x==MINIMAP_X && y==MINIMAP_Y &&
          w==MINIMAP_W && h==MINIMAP_H && color==0xff123456UL);
    CHECK(g_owner_bitmap_scope.object_ptr==(DWORD)(ULONG_PTR)&minimap_window);
    CHECK(g_owner_bitmap_scope.thread==17);
    manager_scope=g_owner_bitmap_scope;
    ++manager_calls;
    expected_renderer=&renderer; expected_primitive=&manager_primitive; expected_flags=0x2ff;
    owner_bitmap_queue_scoped(expected_renderer,&manager_primitive,expected_flags);
    return 0x2468ace0UL;
}

static void fixture_reset(unsigned int percent) {
    DWORD i;
    memset(g_owner_bitmap_draws,0,sizeof(g_owner_bitmap_draws));
    memset(&g_owner_bitmap_scope,0,sizeof(g_owner_bitmap_scope));
    memset(states,0,sizeof(states));
    g_owner_bitmap_lock=0; g_ui_present_serial=100; current_thread=17;
    g_owner_bitmap_calls=g_owner_bitmap_submits=g_owner_bitmap_matched=0;
    g_owner_bitmap_overflow=g_owner_bitmap_expired=g_owner_bitmap_mismatched=0;
    g_owner_bitmap_unsupported=g_owner_bitmap_peak=g_owner_bitmap_offscreen=0;
    g_owner_bitmap_unowned=g_owner_bitmap_order=g_owner_bitmap_active_count=0;
    g_owner_bitmap_frame_calls=g_owner_minimap_draws=0;
    g_owner_input_order=0;
    g_owner_submit_enabled=g_owner_scale_enabled=g_owner_tooltip_enabled=1;
    g_owner_bitmap_hooks_installed=1;
    g_ui_enabled=g_ui_runtime_enabled=1;
    g_ui_scale_global=0; g_ui_scale_unmatched=0;
    g_ui_screen_w=3440; g_ui_screen_h=1440;
    g_ui_origin_x=g_ui_origin_y=0; g_ui_anchor_mode=1;
    g_ui_global_threshold_percent=75; g_ui_scale_percent=(int)percent;
    g_owner_tagged_draws=g_ui_scaled_draws=0;
    fallback_collected=legacy_matches=legacy_collected=trace_calls=0;
    legacy_match_result=0; unreadable=0; g_GetCurrentThreadId=thread_id;
    g_ui_frame_rect_count=g_owner_frame_member_count=present_notifications=0;
    set_window(&minimap_window,MINIMAP_X,MINIMAP_Y,MINIMAP_W,MINIMAP_H);
    set_window(&wrong_window,MINIMAP_X,MINIMAP_Y,MINIMAP_W,MINIMAP_H);
    set_window(&unreadable_window,MINIMAP_X,MINIMAP_Y,MINIMAP_W,MINIMAP_H);
    memset(&scene,0,sizeof(scene));
    states[1].object_ptr=(DWORD)(ULONG_PTR)&minimap_window;
    states[1].vtable_ptr=0x10001000UL; strcpy(states[1].class_name,"UIMinimapZoomWnd");
    states[2].object_ptr=(DWORD)(ULONG_PTR)&wrong_window;
    states[2].vtable_ptr=0x10002000UL; strcpy(states[2].class_name,"UIStatusWnd");
    states[3].object_ptr=(DWORD)(ULONG_PTR)&unreadable_window;
    states[3].vtable_ptr=0x10003000UL; strcpy(states[3].class_name,"UIMinimapZoomWnd");
    set_lookup(&minimap_window);
    g_exe=(HMODULE)exe_fixture; g_exe_size=PRM_MINIMAP_WINDOW_RVA+4;
    g_owner_minimap_draw=native_minimap; g_owner_bitmap_submit=native_queue;
    scene_calls=manager_calls=queue_calls=0; expect_valid=1;
    memset(&direct_scope,0,sizeof(direct_scope));
    memset(&manager_scope,0,sizeof(manager_scope));
    quad_depth(&direct_quads[0],MINIMAP_X+1,MINIMAP_Y-1,128,128,0.8f,0.1f);
    marker_quad(&direct_quads[1],MINIMAP_X+5,145);
    quad_depth(&direct_quads[2],MINIMAP_X+50,145,16,10,0.8f,0.1f);
    quad_depth(&direct_quads[3],MINIMAP_X+72,145,16,10,0.8f,0.1f);
    quad_depth(&manager_quad,MINIMAP_X,MINIMAP_Y,MINIMAP_W,MINIMAP_H,0.0f,1.0f);
    for(i=0;i<4;++i) { direct_primitives[i].verts=&direct_quads[i]; direct_primitives[i].count=4; }
    manager_primitive.verts=&manager_quad; manager_primitive.count=4;
}
static void assert_scope_equal(const OwnerBitmapScope* a,const OwnerBitmapScope* b) {
    CHECK(!memcmp(a,b,sizeof(*a)));
}
static void assert_scope(const OwnerBitmapScope* scope) {
    CHECK(scope->object_ptr==(DWORD)(ULONG_PTR)&minimap_window);
    CHECK(scope->vtable_ptr==0x10001000UL && scope->thread==17);
    CHECK(fabsf(scope->ax-3440.0f)<0.001f && fabsf(scope->ay)<0.001f);
    CHECK(!scope->native_size);
}
static const void* scale_quad(Quad* q,Quad* out) {
    return make_scaled_ui_vertices(5,0x1c4,q,4,out->bytes,sizeof(*out),0,0);
}
static void assert_transformed(const Quad* before,const Quad* out,float ax,float ay) {
    DWORD i,j; float s=ui_scale_factor();
    for(i=0;i<4;++i) {
        CHECK(fabsf(out->f[i][0]-(ax+(before->f[i][0]-ax)*s))<0.001f);
        CHECK(fabsf(out->f[i][1]-(ay+(before->f[i][1]-ay)*s))<0.001f);
        for(j=2;j<8;++j) CHECK(out->d[i][j]==before->d[i][j]);
    }
}

static void valid_minimap(unsigned int percent) {
    OwnerBitmapScope outer; Quad before,out; DWORD i;
    fixture_reset(percent); outer_scope(&outer); g_owner_bitmap_scope=outer;
    CHECK(!looks_like_ui_vertices(5,0x1c4,&direct_quads[0],4));
    CHECK(owner_minimap_draw_scoped(&scene)==0x13579bdfUL);
    CHECK(scene_calls==1 && g_owner_minimap_draws==1 && queue_calls==4);
    assert_scope(&direct_scope); assert_scope_equal(&g_owner_bitmap_scope,&outer);
    CHECK(states[1].pos_x==MINIMAP_X && states[1].pos_y==MINIMAP_Y);
    CHECK(states[1].input_local_bbox.r==128 && states[1].input_local_bbox.b==140);
    CHECK(states[1].frame_bbox.l==MINIMAP_X && states[1].frame_bbox.t==MINIMAP_Y);
    CHECK(states[1].frame_bbox.r==MINIMAP_X+MINIMAP_W &&
          states[1].frame_bbox.b==MINIMAP_Y+MINIMAP_H);

    CHECK(owner_bitmap_draw_c((DWORD)(ULONG_PTR)&minimap_window,(void*)&manager_dc,
          (void*)native_manager_bitmap,MINIMAP_X,MINIMAP_Y,MINIMAP_W,MINIMAP_H,
          0xff123456UL)==0x2468ace0UL);
    CHECK(manager_calls==1 && queue_calls==5);
    assert_scope(&manager_scope); assert_scope_equal(&direct_scope,&manager_scope);
    assert_scope_equal(&g_owner_bitmap_scope,&outer);
    CHECK(g_owner_bitmap_active_count==5);
    /* Deferred draws must retain the transform captured when they were queued. */
    states[1].ax=100; states[1].ay=200; states[1].pos_x=300; states[1].pos_y=400;
    for(i=0;i<4;++i) {
        before=direct_quads[i]; memset(&out,0,sizeof(out));
        CHECK(scale_quad(&direct_quads[i],&out)==&out);
        assert_transformed(&before,&out,direct_scope.ax,direct_scope.ay);
        CHECK(!memcmp(&direct_quads[i],&before,sizeof(before)));
    }
    before=manager_quad; memset(&out,0,sizeof(out));
    CHECK(scale_quad(&manager_quad,&out)==&out);
    assert_transformed(&before,&out,manager_scope.ax,manager_scope.ay);
    CHECK(!memcmp(&manager_quad,&before,sizeof(before)));
    CHECK(g_owner_bitmap_matched==5 && !g_owner_bitmap_active_count);
    CHECK(g_ui_scaled_draws==5 && !g_owner_bitmap_unowned && !g_owner_bitmap_mismatched);
}

static void invalid_owner(unsigned int kind) {
    OwnerBitmapScope outer;
    fixture_reset(133); outer_scope(&outer); g_owner_bitmap_scope=outer;
    if(kind==0) set_lookup(&wrong_window);
    else if(kind==1) set_lookup(0);
    else if(kind==2) { set_lookup(&unreadable_window); unreadable=(BYTE*)&unreadable_window+0x14; }
    else if(kind==3) { set_lookup(&minimap_window); unreadable=exe_fixture+PRM_MINIMAP_WINDOW_RVA; }
    else { g_exe=0; }
    expect_valid=0;
    CHECK(owner_minimap_draw_scoped(&scene)==0x13579bdfUL);
    CHECK(scene_calls==1 && g_owner_minimap_draws==1 && queue_calls==4);
    assert_scope_equal(&g_owner_bitmap_scope,&outer);
    CHECK(!g_owner_bitmap_active_count && !g_owner_bitmap_frame_calls);
    CHECK(g_owner_bitmap_unowned==4 && !g_owner_bitmap_matched);
}

static void disabled_paths(void) {
    OwnerBitmapScope outer; Quad before,out; DWORD i;
    fixture_reset(133); outer_scope(&outer); g_owner_bitmap_scope=outer;
    g_ui_runtime_enabled=0;
    CHECK(owner_minimap_draw_scoped(&scene)==0x13579bdfUL);
    CHECK(scene_calls==1 && queue_calls==4 && g_owner_bitmap_active_count==4);
    assert_scope_equal(&g_owner_bitmap_scope,&outer);
    for(i=0;i<4;++i) {
        before=direct_quads[i]; memset(&out,0,sizeof(out));
        CHECK(scale_quad(&direct_quads[i],&out)==&direct_quads[i]);
        CHECK(!memcmp(&direct_quads[i],&before,sizeof(before)));
    }
    CHECK(!g_ui_scaled_draws && g_owner_bitmap_matched==4 && !g_owner_bitmap_active_count);

    fixture_reset(200); outer_scope(&outer); g_owner_bitmap_scope=outer;
    g_ui_enabled=0;
    CHECK(owner_minimap_draw_scoped(&scene)==0x13579bdfUL);
    CHECK(scene_calls==1 && queue_calls==4 && g_owner_bitmap_active_count==4);
    for(i=0;i<4;++i) {
        before=direct_quads[i]; memset(&out,0,sizeof(out));
        CHECK(scale_quad(&direct_quads[i],&out)==&direct_quads[i]);
        CHECK(!memcmp(&direct_quads[i],&before,sizeof(before)));
    }
    CHECK(!g_ui_scaled_draws && g_owner_bitmap_matched==4 && !g_owner_bitmap_active_count);

    fixture_reset(133); outer_scope(&outer); g_owner_bitmap_scope=outer;
    g_owner_bitmap_hooks_installed=0; expect_valid=0;
    CHECK(owner_minimap_draw_scoped(&scene)==0x13579bdfUL);
    CHECK(scene_calls==1 && queue_calls==4 && g_owner_bitmap_unowned==4);
    assert_scope_equal(&g_owner_bitmap_scope,&outer);
}

int main(void) {
    unsigned int percent;
    CHECK(sizeof(void*)==4 && sizeof(Primitive)==8 && sizeof(Quad)==128);
    exe_fixture=(BYTE*)calloc(PRM_MINIMAP_WINDOW_RVA+4,1); CHECK(exe_fixture);
    for(percent=133;percent<=200;percent+=67) valid_minimap(percent);
    invalid_owner(0); invalid_owner(1); invalid_owner(2); invalid_owner(3); invalid_owner(4);
    disabled_paths();
    free(exe_fixture); exe_fixture=0; g_exe=0;
    puts("PASS minimap ownership: 32-bit scene forwarding, exact UIMinimapZoomWnd lookup, native 128x140 right-edge anchor, frozen image/marker/control and manager bitmap transform at 133%/200%, four-vertex z/RHW provenance, scope restoration, invalid owner isolation, disabled scaling");
    return 0;
}
"""


def main():
    with tempfile.TemporaryDirectory(prefix="prm-minimap-test-") as directory:
        c_file = Path(directory) / "minimap_test.c"
        binary = Path(directory) / "minimap_test"
        c_file.write_text(prefix + types + stubs + production + tests)
        subprocess.run([
            os.environ.get("CC", "clang"), "-m32", "-std=c11", "-O1", "-g",
            "-Wall", "-Wextra", "-Wno-unused-variable", "-Wno-unused-parameter",
            "-Wno-unused-function", "-fsanitize=address,undefined",
            "-fno-omit-frame-pointer", str(c_file), "-o", str(binary),
        ], check=True)
        env = os.environ.copy()
        env.setdefault("ASAN_OPTIONS", "detect_leaks=0")
        subprocess.run([str(binary)], check=True, env=env)


if __name__ == "__main__":
    main()
