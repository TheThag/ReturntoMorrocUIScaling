#!/usr/bin/env python3
"""Exercise production bitmap ownership and scaler integration with ASan/UBSan.

The registry, scope preparation, anchoring, and final vertex scaler are extracted
from prm_uifix.c. Windows object lookup and unrelated fallback services use
explicit host stubs; this does not replace native ABI or visual verification.
"""

from pathlib import Path
import os
import re
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parent
source = (ROOT / "prm_uifix.c").read_text()


def function(name):
    match = re.search(r"^(?:static )?[^\n]*\b" + re.escape(name) + r"\([^;]*?\)\s*\{", source, re.M)
    if not match:
        raise RuntimeError(f"Cannot extract production function: {name}")
    depth, end = 1, match.end()
    while depth:
        depth += (source[end] == "{") - (source[end] == "}")
        end += 1
    return source[match.start():end]


def struct_type(name):
    end = source.index("} " + name + ";") + len("} " + name + ";")
    start = source.rfind("typedef struct {", 0, end)
    return source[start:end]


def constant(name):
    match = re.search(r"^#define " + re.escape(name) + r"\s+[^\n]+", source, re.M)
    if not match:
        raise RuntimeError(f"Cannot extract production constant: {name}")
    return match[0]


start = source.index("static int g_owner_bitmap_enabled=")
end = source.index("#define MAX_OWNER_CAPTURE_LINKS", start)
types = struct_type("OwnerWindowState") + "\n" + source[start:end]
types += "\n" + "\n".join(constant(name) for name in (
    "OWNER_BITMAP_PROBES", "PRM_OFFSCREEN_DP_RETURN_RVA", "PRM_OFFSCREEN_DIP_RETURN_RVA",
))
production = "\n".join(function(name) for name in (
    "f_abs", "fvf_stride", "ui_scale_factor", "rect_is_global", "choose_group_anchor",
    "owner_class_is_hover_popup", "owner_class_is_world_label", "owner_class_is_world_title", "owner_class_is_world_name", "owner_class_should_hook",
    "owner_input_touch_state", "owner_bitmap_prepare",
    "owner_bitmap_draw_c", "owner_bitmap_registry_lock", "owner_bitmap_registry_unlock",
    "owner_bitmap_bucket", "owner_bitmap_forget", "owner_bitmap_note_vertices",
    "owner_bitmap_consume_vertices", "looks_like_ui_vertices", "make_scaled_ui_vertices",
    "clear_ui_frame_accumulator", "hook_SurfaceBltFast",
))

prefix = r"""
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <math.h>
typedef uint32_t DWORD;
typedef int32_t LONG;
typedef unsigned char BYTE;
typedef uintptr_t ULONG_PTR;
typedef struct { float l,t,r,b; } UIRectF;
typedef struct { LONG left,top,right,bottom; } RECT;
typedef LONG HRESULT;
typedef DWORD (*PFN_BitmapDraw)(void*,LONG,LONG,LONG,LONG,DWORD);
typedef HRESULT (*PFN_DDS7_BltFast)(void*,DWORD,DWORD,void*,RECT*,DWORD);
typedef struct { void* orig_bltfast; } SurfHookRec;
#define WINAPI
#define CHECK(x) do { if (!(x)) { \
    fprintf(stderr,"check failed at line %d: %s\n",__LINE__,#x); exit(1); \
} } while (0)
static DWORD g_ui_present_serial,g_owner_input_order;
static int g_owner_submit_enabled,g_owner_scale_enabled,g_owner_tooltip_enabled;
static int g_ui_enabled,g_ui_runtime_enabled,g_ui_scale_global,g_ui_scale_unmatched;
static LONG g_ui_screen_w,g_ui_screen_h,g_ui_origin_x,g_ui_origin_y;
static int g_ui_anchor_mode,g_ui_global_threshold_percent,g_ui_scale_percent;
static DWORD g_owner_tagged_draws,g_ui_scaled_draws;
static DWORD g_ui_frame_rect_count,g_owner_frame_member_count;
static DWORD thread_id(void) { return 17; }
static DWORD (*g_GetCurrentThreadId)(void)=thread_id;
static const void* unreadable;
static int mem_readable(const void* p,DWORD n) { return p && p!=unreadable && n<=128; }
static int s_contains(const char* s,const char* p) { return strstr(s,p)!=0; }
static int s_equal(const char* a,const char* b) { return strcmp(a,b)==0; }
"""

stubs = r"""
/* Host object identities are small IDs; production state and behavior remain
   unchanged after the native object/RTTI lookup boundary. */
static OwnerWindowState states[8];
static DWORD fallback_collected,legacy_matches,legacy_collected,trace_calls;
static int legacy_match_result;
static OwnerWindowState* owner_state_for(DWORD obj,int create) {
    OwnerWindowState* st;
    if(!obj || obj>=8) return 0;
    st=&states[obj];
    if(!st->object_ptr && create) {
        st->object_ptr=obj; st->vtable_ptr=obj*4096;
        strcpy(st->class_name,"UIItemWnd");
    }
    return st->object_ptr?st:0;
}
static int cursor_consume_vertices(DWORD fvf,const void* v,DWORD n) {
    (void)fvf;(void)v;(void)n; return 0;
}
static void vtrace_note_d3d_ui(void) { ++trace_calls; }
static int owner_submit_match_rect(const UIRectF* r,DWORD* obj) {
    (void)r; ++legacy_matches; *obj=1; return legacy_match_result;
}
static void owner_collect_rect(DWORD obj,const UIRectF* r) {
    (void)obj;(void)r; ++legacy_collected;
}
static int owner_get_transform(DWORD obj,float* ax,float* ay) {
    (void)obj; *ax=123; *ay=456; return 1;
}
static void collect_ui_rect(float a,float b,float c,float d) {
    (void)a;(void)b;(void)c;(void)d; ++fallback_collected;
}
static int get_group_transform_for_rect(const UIRectF* r,float* ax,float* ay) {
    (void)r;(void)ax;(void)ay; return 0;
}
static SurfHookRec surface_rec;
static DWORD present_notifications;
static SurfHookRec* surf_rec(void* self) { (void)self; return &surface_rec; }
static int surface_is_screenish(void* self) { return self!=0; }
static void ui_present_boundary(const char* kind) {
    CHECK(!strcmp(kind,"BltFast")); ++present_notifications;
}
"""

tests = r"""
typedef union { DWORD d[4][8]; float f[4][8]; BYTE bytes[128]; } Quad;
static void reset(void) {
    memset(g_owner_bitmap_draws,0,sizeof(g_owner_bitmap_draws));
    memset(&g_owner_bitmap_scope,0,sizeof(g_owner_bitmap_scope));
    memset(states,0,sizeof(states));
    g_owner_bitmap_lock=0; g_ui_present_serial=100;
    g_owner_bitmap_calls=g_owner_bitmap_submits=g_owner_bitmap_matched=0;
    g_owner_bitmap_overflow=g_owner_bitmap_expired=g_owner_bitmap_mismatched=0;
    g_owner_bitmap_unsupported=g_owner_bitmap_peak=g_owner_bitmap_offscreen=0;
    g_owner_bitmap_unowned=g_owner_bitmap_order=g_owner_bitmap_active_count=0;
    g_owner_bitmap_frame_calls=g_owner_input_order=0;
    g_owner_submit_enabled=g_owner_scale_enabled=g_owner_tooltip_enabled=1;
    g_owner_bitmap_hooks_installed=g_ui_enabled=g_ui_runtime_enabled=1;
    g_ui_scale_global=1; g_ui_scale_unmatched=0;
    g_ui_screen_w=1920; g_ui_screen_h=1080;
    g_ui_origin_x=g_ui_origin_y=0; g_ui_anchor_mode=1;
    g_ui_global_threshold_percent=75; g_ui_scale_percent=133;
    g_owner_tagged_draws=g_ui_scaled_draws=0;
    fallback_collected=legacy_matches=legacy_collected=trace_calls=0;
    legacy_match_result=0; unreadable=0; g_GetCurrentThreadId=thread_id;
    g_ui_frame_rect_count=g_owner_frame_member_count=present_notifications=0;
    surface_rec.orig_bltfast=0;
}
static void quad(Quad* q,float x,float y,float w,float h) {
    DWORD i; memset(q,0,sizeof(*q));
    for(i=0;i<4;++i) {
        q->f[i][0]=x+((i&1)?w:0); q->f[i][1]=y+((i&2)?h:0);
        q->f[i][2]=0.00001f; q->f[i][3]=0.99999f;
        q->d[i][4]=0xffffffff; q->d[i][5]=0xff000000;
        q->f[i][6]=(i&1)?1:0; q->f[i][7]=(i&2)?1:0;
    }
}
static void tag(Quad* q) { owner_bitmap_note_vertices(q,4,&g_owner_bitmap_scope); }
static int consume(Quad* q,float* ax,float* ay) {
    return owner_bitmap_consume_vertices(0x1c4,q,4,ax,ay);
}
static const void* scale(Quad* q,Quad* out,DWORD caller) {
    return make_scaled_ui_vertices(5,0x1c4,q,4,out->bytes,sizeof(*out),0,caller);
}
static void transformed(const Quad* original,const Quad* out,float ax,float ay) {
    DWORD i,j; float s=ui_scale_factor();
    for(i=0;i<4;++i) {
        CHECK(fabsf(out->f[i][0]-(ax+(original->f[i][0]-ax)*s))<0.001f);
        CHECK(fabsf(out->f[i][1]-(ay+(original->f[i][1]-ay)*s))<0.001f);
        for(j=2;j<8;++j) CHECK(out->d[i][j]==original->d[i][j]);
    }
}
static void split_tiles(void) {
    Quad left,right,left_before,right_before,a,b; UIRectF tile_bbox;
    float wrong_ax,wrong_ay; OwnerBitmapScope frozen;
    reset(); CHECK(owner_bitmap_prepare(1,540,200,280,200));
    frozen=g_owner_bitmap_scope;
    CHECK(frozen.ax==960 && frozen.ay==0 && frozen.object_ptr==1 && frozen.thread==17);
    CHECK(g_owner_bitmap_frame_calls==1 && states[1].last_input_order==1);
    CHECK(states[1].frame_bbox.r==820 && states[1].input_local_bbox.r==280);
    CHECK(states[1].bitmap_present==101 && states[1].last_draw_present==101);
    quad(&left,540,200,256,200); quad(&right,796,200,24,200);
    left_before=left; right_before=right;
    tile_bbox=(UIRectF){540,200,796,400};
    choose_group_anchor(&tile_bbox,&wrong_ax,&wrong_ay);
    CHECK(wrong_ax!=frozen.ax); /* The old independent tile transform disagrees. */
    tag(&left); tag(&right);
    /* State moves before deferred rendering; both tags retain their snapshot. */
    states[1].ax=1920; states[1].ay=1080;
    CHECK(scale(&right,&b,0)==&b); CHECK(scale(&left,&a,0)==&a);
    transformed(&left,&a,frozen.ax,frozen.ay); transformed(&right,&b,frozen.ax,frozen.ay);
    CHECK(a.f[1][0]==b.f[0][0] && a.f[3][0]==b.f[2][0]);
    CHECK(!memcmp(&left,&left_before,sizeof(left)) && !memcmp(&right,&right_before,sizeof(right)));
    CHECK(!fallback_collected && !legacy_matches && g_owner_bitmap_matched==2);
    CHECK(g_owner_bitmap_active_count==0);
}
static void offscreen_tiles(void) {
    Quad left,right,a,b; float ax,ay;
    reset(); CHECK(owner_bitmap_prepare(1,-200,200,280,200));
    ax=g_owner_bitmap_scope.ax; ay=g_owner_bitmap_scope.ay;
    quad(&left,-200,200,256,200); quad(&right,56,200,24,200);
    CHECK(!looks_like_ui_vertices(5,0x1c4,&left,4));
    CHECK(looks_like_ui_vertices(5,0x1c4,&right,4));
    tag(&left); tag(&right);
    CHECK(scale(&left,&a,0)==&a && scale(&right,&b,0)==&b);
    transformed(&left,&a,ax,ay); transformed(&right,&b,ax,ay);
    CHECK(a.f[1][0]==b.f[0][0] && !fallback_collected);
}
static void overlap_and_identity(void) {
    Quad a,b,c; float ax,ay;
    reset(); CHECK(owner_bitmap_prepare(1,10,20,100,100));
    CHECK(owner_bitmap_prepare(2,1700,20,100,100));
    CHECK(states[1].ax==0 && states[2].ax==1920);
    quad(&a,540,200,100,100); b=a; c=a;
    CHECK(owner_bitmap_prepare(1,540,200,100,100)); tag(&a);
    CHECK(owner_bitmap_prepare(2,540,200,100,100)); tag(&b);
    CHECK(!consume(&c,&ax,&ay)); /* Same content is not ownership. */
    CHECK(consume(&b,&ax,&ay)==1 && ax==1920 && ay==0);
    CHECK(consume(&a,&ax,&ay)==1 && ax==0 && ay==0);
    CHECK(!consume(&a,&ax,&ay));
}
static void fingerprint_and_reuse(void) {
    Quad a; float ax,ay; DWORD i,j; const DWORD fields[]={0,1,2,3,6,7};
    for(i=0;i<4;++i) for(j=0;j<6;++j) {
        reset(); CHECK(owner_bitmap_prepare(1,10,20,100,100)); quad(&a,10,20,100,100); tag(&a);
        a.d[i][fields[j]]^=1; CHECK(!consume(&a,&ax,&ay));
        CHECK(g_owner_bitmap_mismatched==1 && g_owner_bitmap_active_count==0);
        a.d[i][fields[j]]^=1; CHECK(!consume(&a,&ax,&ay));
    }
    reset(); CHECK(owner_bitmap_prepare(1,10,20,100,100)); quad(&a,10,20,100,100); tag(&a);
    for(i=0;i<4;++i) { a.d[i][4]^=0xffffffff; a.d[i][5]^=0xffffffff; }
    CHECK(consume(&a,&ax,&ay)==1); /* Native diffuse/specular mutations are allowed. */
    tag(&a); owner_bitmap_note_vertices(&a,4,0); CHECK(!consume(&a,&ax,&ay));
    tag(&a); owner_bitmap_note_vertices(&a,3,&g_owner_bitmap_scope); CHECK(!consume(&a,&ax,&ay));
    CHECK(g_owner_bitmap_unsupported==1);
    tag(&a); unreadable=&a; tag(&a); unreadable=0; CHECK(!consume(&a,&ax,&ay));
    CHECK(g_owner_bitmap_unsupported==2);
    tag(&a); CHECK(!owner_bitmap_consume_vertices(0x2c4,&a,4,&ax,&ay));
    CHECK(!consume(&a,&ax,&ay));
    tag(&a); CHECK(!owner_bitmap_consume_vertices(0x1c4,&a,3,&ax,&ay));
    tag(&a); CHECK(owner_bitmap_prepare(2,1700,20,100,100));
    quad(&a,1700,20,100,100); tag(&a);
    CHECK(consume(&a,&ax,&ay)==1 && ax==1920);
    CHECK(g_owner_bitmap_peak==1 && g_owner_bitmap_active_count==0);
    owner_bitmap_note_vertices(0,4,&g_owner_bitmap_scope); CHECK(!consume(0,&ax,&ay));
}
static void lifetime(void) {
    Quad a; float ax,ay;
    reset(); CHECK(owner_bitmap_prepare(1,10,20,100,100)); quad(&a,10,20,100,100);
    tag(&a); g_ui_present_serial+=2; CHECK(consume(&a,&ax,&ay)==1);
    tag(&a); g_ui_present_serial+=3; CHECK(!consume(&a,&ax,&ay));
    CHECK(g_owner_bitmap_expired==1);
    tag(&a); g_ui_present_serial+=3; tag(&a); CHECK(g_owner_bitmap_expired==2);
    CHECK(consume(&a,&ax,&ay)==1 && g_owner_bitmap_active_count==0);
    g_ui_present_serial=UINT32_MAX-1; tag(&a); g_ui_present_serial=0;
    CHECK(consume(&a,&ax,&ay)==1);
    g_ui_present_serial=UINT32_MAX-1; tag(&a); g_ui_present_serial=1;
    CHECK(!consume(&a,&ax,&ay) && g_owner_bitmap_expired==3);
}
static void bounded_collisions(void) {
    size_t step=MAX_OWNER_BITMAP_DRAWS*16; DWORD i; float ax,ay;
    BYTE* pool=malloc(step*OWNER_BITMAP_PROBES+sizeof(Quad)); CHECK(pool);
    reset(); CHECK(owner_bitmap_prepare(1,10,20,100,100));
    for(i=0;i<=OWNER_BITMAP_PROBES;++i) {
        Quad* q=(Quad*)(pool+i*step); quad(q,10,20,100,100);
        CHECK(owner_bitmap_bucket(q)==owner_bitmap_bucket(pool)); tag(q);
    }
    CHECK(g_owner_bitmap_active_count==OWNER_BITMAP_PROBES);
    CHECK(g_owner_bitmap_peak==OWNER_BITMAP_PROBES && g_owner_bitmap_overflow==1);
    CHECK(!consume((Quad*)(pool+OWNER_BITMAP_PROBES*step),&ax,&ay));
    CHECK(consume((Quad*)pool,&ax,&ay)==1); /* Hole must not terminate later lookup. */
    tag((Quad*)(pool+OWNER_BITMAP_PROBES*step));
    for(i=OWNER_BITMAP_PROBES;i>0;--i) CHECK(consume((Quad*)(pool+i*step),&ax,&ay)==1);
    CHECK(!g_owner_bitmap_active_count);
    free(pool);
}
static void full_capacity(void) {
    DWORD i; float ax,ay;
    Quad* pool=malloc((MAX_OWNER_BITMAP_DRAWS+1)*sizeof(Quad)); CHECK(pool);
    reset(); CHECK(owner_bitmap_prepare(1,10,20,100,100));
    CHECK(!(MAX_OWNER_BITMAP_DRAWS&(MAX_OWNER_BITMAP_DRAWS-1)));
    CHECK(OWNER_BITMAP_PROBES<=MAX_OWNER_BITMAP_DRAWS);
    for(i=0;i<=MAX_OWNER_BITMAP_DRAWS;++i) { quad(&pool[i],10,20,100,100); tag(&pool[i]); }
    CHECK(g_owner_bitmap_peak==MAX_OWNER_BITMAP_DRAWS && g_owner_bitmap_overflow==1);
    CHECK(!consume(&pool[MAX_OWNER_BITMAP_DRAWS],&ax,&ay));
    for(i=0;i<MAX_OWNER_BITMAP_DRAWS;++i) CHECK(consume(&pool[i],&ax,&ay)==1);
    CHECK(!g_owner_bitmap_active_count); free(pool);
}
static void prepare_gates_and_popup(void) {
    reset(); CHECK(owner_bitmap_prepare(1,10,20,100,100));
    g_owner_bitmap_hooks_installed=0; CHECK(!owner_bitmap_prepare(1,10,20,100,100));
    CHECK(!g_owner_bitmap_scope.object_ptr && !g_owner_bitmap_scope.thread);
    g_owner_bitmap_hooks_installed=1; g_owner_submit_enabled=0;
    CHECK(!owner_bitmap_prepare(1,10,20,100,100)); g_owner_submit_enabled=1;
    g_owner_scale_enabled=0; CHECK(!owner_bitmap_prepare(1,10,20,100,100)); g_owner_scale_enabled=1;
    CHECK(!owner_bitmap_prepare(1,10,20,0,100));
    CHECK(!owner_bitmap_prepare(1,-8193,20,100,100));
    CHECK(!owner_bitmap_prepare(1,10,20,8193,100));
    CHECK(!owner_bitmap_prepare(0,10,20,100,100));
    CHECK(g_owner_bitmap_frame_calls==1 && g_owner_bitmap_unsupported==3);
    strcpy(states[2].class_name,"UISkillDescribeWnd"); states[2].object_ptr=2;
    g_owner_tooltip_enabled=0; CHECK(!owner_bitmap_prepare(2,450,310,100,100));
    g_owner_tooltip_enabled=1; CHECK(owner_bitmap_prepare(2,450,310,100,100));
    CHECK(g_owner_bitmap_scope.ax==450 && g_owner_bitmap_scope.ay==310);
    CHECK(!states[2].last_input_order); /* Visual hover popup does not take input. */
}
static void scaler_integration(void) {
    Quad a,out; float ax,ay; DWORD offscreen[]={PRM_OFFSCREEN_DP_RETURN_RVA,PRM_OFFSCREEN_DIP_RETURN_RVA},i;
    reset(); CHECK(owner_bitmap_prepare(1,10,20,100,100)); quad(&a,10,20,100,100);
    tag(&a); g_ui_runtime_enabled=0; CHECK(scale(&a,&out,0)==&a);
    CHECK(g_owner_bitmap_matched==1 && !g_owner_bitmap_active_count && !fallback_collected);
    g_ui_runtime_enabled=1; CHECK(scale(&a,&out,0)==&a);
    CHECK(fallback_collected==1 && !legacy_matches);
    tag(&a); g_ui_enabled=0; CHECK(scale(&a,&out,0)==&a);
    CHECK(!g_owner_bitmap_active_count); g_ui_enabled=1;
    for(i=0;i<2;++i) {
        tag(&a); CHECK(scale(&a,&out,offscreen[i])==&a);
        CHECK(g_owner_bitmap_active_count==1); CHECK(consume(&a,&ax,&ay)==1);
    }
    CHECK(g_owner_bitmap_offscreen==2);
    legacy_match_result=1; CHECK(scale(&a,&out,0)==&a); CHECK(!legacy_matches);
    g_owner_bitmap_hooks_installed=0; CHECK(scale(&a,&out,0)==&out);
    CHECK(legacy_matches==1 && legacy_collected==1);
    transformed(&a,&out,123,456);
    reset(); g_ui_scale_global=0;
    CHECK(owner_bitmap_prepare(1,0,0,1920,100)); CHECK(g_owner_bitmap_scope.native_size);
    CHECK(!states[1].last_input_order); quad(&a,512,0,256,100); tag(&a);
    CHECK(consume(&a,&ax,&ay)==2); tag(&a);
    CHECK(scale(&a,&out,0)==&a && !fallback_collected && !legacy_matches && !trace_calls);
    CHECK(!g_owner_bitmap_active_count);
    CHECK(owner_bitmap_prepare(1,10,20,100,100) && !g_owner_bitmap_scope.native_size);
    CHECK(states[1].last_input_order); /* Resized normal window becomes interactive. */
}
static void npc_world_labels(void) {
    Quad plaque,before,out,tiles[3]; DWORD i; OwnerWindowState* st;
    const LONG positions[][2]={{1268,498},{2178,1190},{1803,1483},{-200,200}};
    reset();
    CHECK(owner_class_is_world_label("CSignBoardWnd"));
    CHECK(owner_class_should_hook("CSignBoardWnd"));
    CHECK(!owner_class_is_world_label(0) && !owner_class_is_world_label(""));
    CHECK(!owner_class_is_world_label("CSignBoardWndOther"));
    CHECK(!owner_class_is_world_label("OtherCSignBoardWnd"));
    CHECK(!owner_class_should_hook("CBmpObjWnd"));
    CHECK(owner_class_should_hook("UIItemWnd") && !owner_class_is_world_label("UIItemWnd"));
    st=owner_state_for(1,1); strcpy(st->class_name,"CSignBoardWnd");
    st->last_input_order=77; /* Passive world labels revoke stale input ownership. */
    for(i=0;i<4;++i) {
        const float ax=(float)(positions[i][0]+81),ay=(float)(positions[i][1]+18);
        g_ui_scale_global=i&1;
        CHECK(owner_bitmap_prepare(1,positions[i][0],positions[i][1],162,36));
        CHECK(!g_owner_bitmap_scope.native_size && !st->last_input_order);
        CHECK(st->ax==ax && st->ay==ay);
        CHECK(g_owner_bitmap_scope.ax==ax && g_owner_bitmap_scope.ay==ay);
        CHECK(st->pos_x==positions[i][0] && st->pos_y==positions[i][1]);
        owner_input_touch_state(st); CHECK(!st->last_input_order);
        quad(&plaque,(float)positions[i][0],(float)positions[i][1],162,36); before=plaque;
        tag(&plaque); CHECK(scale(&plaque,&out,0)==&out);
        transformed(&plaque,&out,ax,ay);
        CHECK(f_abs((out.f[0][0]+out.f[1][0])*0.5f-ax)<0.001f);
        CHECK(!memcmp(&plaque,&before,sizeof(plaque)));
        CHECK(!g_owner_bitmap_active_count && !fallback_collected && !legacy_matches);
    }
    CHECK(!g_owner_input_order && g_owner_tagged_draws==4 && g_ui_scaled_draws==4);
    CHECK(g_owner_bitmap_matched==4);
    /* A larger, odd-size cached label uses the native integer center for every
       tile. Subsequent movement cannot change already queued tile transforms. */
    CHECK(owner_bitmap_prepare(1,3400,600,513,37));
    CHECK(st->ax==3656 && st->ay==618);
    for(i=0;i<3;++i) { quad(&tiles[i],3400.0f+256.0f*i,600,i==2?1:256,37); tag(&tiles[i]); }
    CHECK(owner_bitmap_prepare(1,3500,650,513,37));
    CHECK(st->ax==3756 && st->ay==668);
    for(i=0;i<3;++i) {
        CHECK(scale(&tiles[i],&out,0)==&out);
        transformed(&tiles[i],&out,3656,618);
    }
    CHECK(!g_owner_bitmap_active_count && !st->last_input_order);
    /* Turning scaling off still consumes ownership tags and returns native pixels. */
    tag(&plaque); g_ui_runtime_enabled=0;
    CHECK(scale(&plaque,&out,0)==&plaque && !g_owner_bitmap_active_count);
    g_ui_runtime_enabled=1;
    /* Identical geometry from a regular UI window keeps its ordinary anchor. */
    CHECK(owner_bitmap_prepare(2,1268,498,162,36)); CHECK(!g_owner_bitmap_scope.native_size);
    quad(&plaque,1268,498,162,36); tag(&plaque);
    CHECK(scale(&plaque,&out,0)==&out);
    transformed(&plaque,&out,states[2].ax,states[2].ay);
    CHECK(states[2].last_input_order && g_ui_scaled_draws==8 && !fallback_collected);
}
static void chat_room_titles(void) {
    Quad box,tail,out,old_box; OwnerWindowState* st;
    const LONG positions[][2]={{500,250},{2300,700},{-50,300}};
    DWORD i,order; float old_ax,old_ay;
    reset();
    CHECK(owner_class_is_world_title("UIChatRoomTitle"));
    CHECK(owner_class_should_hook("UIChatRoomTitle"));
    CHECK(!owner_class_is_world_label("UIChatRoomTitle"));
    CHECK(!owner_class_is_world_title(0) && !owner_class_is_world_title("UIChatRoomTitleOther"));
    CHECK(!owner_class_is_world_title("OtherUIChatRoomTitle"));
    CHECK(!owner_class_is_world_title("UIChatRoomWnd"));
    st=owner_state_for(1,1); strcpy(st->class_name,"UIChatRoomTitle");
    for(i=0;i<3;++i) {
        const LONG x=positions[i][0],y=positions[i][1];
        CHECK(owner_bitmap_prepare(1,x,y,140,34));
        CHECK(st->ax==x+70 && st->ay==y+34 && !g_owner_bitmap_scope.native_size);
        CHECK(st->last_input_order && st->last_draw_order);
        CHECK(st->input_local_bbox.r==140 && st->input_local_bbox.b==34);
        order=st->last_input_order;
        owner_input_touch_state(st); CHECK(st->last_input_order>order);
        quad(&box,x,y,140,28); quad(&tail,x+64,y+28,12,6);
        tag(&box); tag(&tail);
        CHECK(scale(&box,&out,0)==&out); transformed(&box,&out,x+70,y+34);
        CHECK(scale(&tail,&out,0)==&out); transformed(&tail,&out,x+70,y+34);
        CHECK(f_abs((out.f[2][0]+out.f[3][0])*0.5f-(x+70))<0.001f);
        CHECK(f_abs(out.f[2][1]-(y+34))<0.001f); /* native pointer tip stays attached */
    }
    CHECK(!fallback_collected && !legacy_matches && !g_owner_bitmap_active_count);
    /* A title and a nearby regular UI retain independent complete transforms. */
    CHECK(owner_bitmap_prepare(1,2300,700,140,34));
    old_ax=st->ax; old_ay=st->ay; quad(&old_box,2300,700,140,34); tag(&old_box);
    CHECK(owner_bitmap_prepare(2,2300,700,140,34));
    CHECK(states[2].ax!=old_ax || states[2].ay!=old_ay);
    CHECK(owner_bitmap_prepare(1,2400,750,140,34)); /* camera/actor moved before queued draw */
    CHECK(scale(&old_box,&out,0)==&out); transformed(&old_box,&out,old_ax,old_ay);
    CHECK(st->ax==2470 && st->ay==784);
}
static void hover_names(void) {
    const char* names[]={"UINameBalloonText","UIVerticalNameBalloonText"};
    const LONG positions[][2]={{500,250},{2300,700},{-50,300},{3400,1400}};
    DWORD n,i; Quad text,out,tiles[3]; OwnerWindowState* st;
    reset();
    CHECK(!owner_class_is_world_name(0) && !owner_class_is_world_name(""));
    CHECK(!owner_class_is_world_name("UINameBalloonTextOther"));
    CHECK(!owner_class_should_hook("OtherUINameBalloonText"));
    CHECK(!owner_class_should_hook("UIBalloonText"));
    CHECK(!owner_class_should_hook("UICharInfoBalloonText"));
    CHECK(!owner_class_is_world_name("CSignBoardWnd"));
    CHECK(!owner_class_is_world_name("UIChatRoomTitle"));
    for(n=0;n<2;++n) {
        CHECK(owner_class_should_hook(names[n]) && owner_class_is_world_name(names[n]));
        st=owner_state_for(1,1); strcpy(st->class_name,names[n]);
        st->have_anchor=1; st->ax=st->ay=0; st->last_input_order=99;
        for(i=0;i<4;++i) {
            LONG x=positions[i][0],y=positions[i][1],w=n?24:120,h=n?120:24;
            CHECK(owner_bitmap_prepare(1,x,y,w,h));
            CHECK(!st->last_input_order && !g_owner_bitmap_scope.native_size);
            owner_input_touch_state(st); CHECK(!st->last_input_order);
            quad(&text,x,y,w,h); tag(&text);
            CHECK(scale(&text,&out,0)==&out);
            /* Enlargement keeps native center while native layout/camera move. */
            CHECK(f_abs((out.f[0][0]+out.f[1][0])*0.5f-(x+w*0.5f))<0.001f);
            CHECK(f_abs((out.f[0][1]+out.f[2][1])*0.5f-(y+h*0.5f))<0.001f);
            CHECK(f_abs((out.f[1][0]-out.f[0][0])-w*1.33f)<0.001f);
        }
        /* Long names/emblems span tiles. Resizing/repositioning the next frame
           must not separate pieces that were queued with the earlier center. */
        CHECK(owner_bitmap_prepare(1,3000,400,513,37));
        for(i=0;i<3;++i) { quad(&tiles[i],3000.0f+256*i,400,i==2?1:256,37); tag(&tiles[i]); }
        CHECK(owner_bitmap_prepare(1,2000,500,120,24));
        for(i=0;i<3;++i) {
            CHECK(scale(&tiles[i],&out,0)==&out);
            transformed(&tiles[i],&out,3256,418);
        }
    }
    CHECK(!g_owner_input_order && !fallback_collected && !legacy_matches && !g_owner_bitmap_active_count);
}
static Quad wrapper_quad;
static DWORD original_draw(void* dc,LONG x,LONG y,LONG w,LONG h,DWORD color) {
    CHECK(dc==(void*)(uintptr_t)42 && x==540 && y==200 && w==280 && h==200 && color==0xff123456);
    CHECK(g_owner_bitmap_scope.object_ptr==1 && g_owner_bitmap_scope.thread==17);
    tag(&wrapper_quad); return 0xabcdef01;
}
static void scope_wrapper(void) {
    OwnerBitmapScope saved; float ax,ay;
    reset(); CHECK(owner_bitmap_prepare(2,1700,20,100,100)); saved=g_owner_bitmap_scope;
    quad(&wrapper_quad,540,200,256,200);
    CHECK(owner_bitmap_draw_c(1,(void*)(uintptr_t)42,(void*)original_draw,540,200,280,200,0xff123456)==0xabcdef01);
    CHECK(!memcmp(&saved,&g_owner_bitmap_scope,sizeof(saved)));
    CHECK(consume(&wrapper_quad,&ax,&ay)==1 && ax==960 && ay==0);
    CHECK(g_owner_bitmap_calls==1 && g_owner_bitmap_frame_calls==2);
    CHECK(owner_bitmap_draw_c(1,0,0,540,200,280,200,0)==0);
    CHECK(!memcmp(&saved,&g_owner_bitmap_scope,sizeof(saved)));
}
static HRESULT original_bltfast(void* self,DWORD x,DWORD y,void* src,RECT* rect,DWORD flags) {
    CHECK(self==(void*)(uintptr_t)1 && x==0 && y==0);
    CHECK(src==(void*)(uintptr_t)2 && rect==0 && flags==7); return 123;
}
static void presentation_activity(void) {
    reset(); CHECK(owner_bitmap_prepare(1,10,20,100,100));
    CHECK(g_owner_bitmap_frame_calls && !g_ui_frame_rect_count && !g_owner_frame_member_count);
    surface_rec.orig_bltfast=(void*)original_bltfast;
    CHECK(hook_SurfaceBltFast((void*)(uintptr_t)1,0,0,(void*)(uintptr_t)2,0,7)==123);
    CHECK(present_notifications==1); /* Owned-only UI still marks presentation activity. */
    clear_ui_frame_accumulator(); CHECK(!g_owner_bitmap_frame_calls);
    CHECK(hook_SurfaceBltFast((void*)(uintptr_t)1,0,0,(void*)(uintptr_t)2,0,7)==123);
    CHECK(present_notifications==1);
}
int main(void) {
    split_tiles(); offscreen_tiles(); overlap_and_identity(); fingerprint_and_reuse();
    lifetime(); bounded_collisions(); full_capacity(); prepare_gates_and_popup();
    scaler_integration(); npc_world_labels(); chat_room_titles(); hover_names(); scope_wrapper(); presentation_activity();
    puts("PASS bitmap ownership: frozen tile transforms, offscreen edges, overlap, identity, 24 immutable fields, colors, reuse, expiry, wrap, bounded collisions, capacity, preparation, disabled scaling, native-size provenance, offscreen bypass, legacy isolation, NPC enlargement at moving attachment and tiled labels, chat-room body/tail attachment and input ownership, normal/vertical hover-name centers and passive input, scope restoration, presentation activity");
    return 0;
}
"""

def main():
    with tempfile.TemporaryDirectory(prefix="prm-bitmap-test-") as directory:
        c_file = Path(directory) / "bitmap_test.c"
        binary = Path(directory) / "bitmap_test"
        c_file.write_text(prefix + types + stubs + production + tests)
        subprocess.run([
            os.environ.get("CC", "clang"), "-std=c11", "-O1", "-g", "-Wall", "-Wextra",
            "-Wno-unused-variable", "-Wno-unused-parameter", "-fsanitize=address,undefined",
            "-fno-omit-frame-pointer", str(c_file), "-o", str(binary),
        ], check=True)
        subprocess.run([str(binary)], check=True)


if __name__ == "__main__":
    main()
