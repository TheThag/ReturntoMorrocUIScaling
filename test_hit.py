#!/usr/bin/env python3
"""Exercise the production owner hit-selection and scoped native-query code.

The generated 32-bit host harness keeps the native side deliberately small:
the fake manager visits Chat before Basic, each candidate dispatches through
its own vtable slot, and the native hit callbacks return either their window
or a child control.  Bounds, order, identity, scope, and coordinate handling
are still the extracted production functions.
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


def extract_definition(source, name):
    """Extract a definition when the source has a same-named declaration."""
    candidates = re.finditer(
        r"^static [^\n]*\b" + re.escape(name) + r"\s*\(", source, re.M)
    for start in candidates:
        opening = source.find("{", start.start())
        if opening < 0 or source.find(";", start.start(), opening) >= 0:
            continue
        tokens = re.finditer(
            r'/\*.*?\*/|//[^\n]*|"(?:\\.|[^"\\])*"|'
            r"'(?:\\.|[^'\\])*'|[{}]",
            source[opening:], re.S)
        depth = 0
        for token in tokens:
            if token[0] == "{":
                depth += 1
            elif token[0] == "}":
                depth -= 1
                if depth == 0:
                    return source[start.start():opening + token.end()]
        raise ValueError(f"unterminated actual source function {name}")
    raise ValueError(f"missing actual source function {name}")


def extract_function_keep_callconv(source, name):
    start = re.search(r"^static [^\n]*\b" + re.escape(name) + r"\s*\(", source, re.M)
    if not start:
        raise ValueError(f"missing actual source function {name}")
    opening = source.index("{", start.start())
    tokens = re.finditer(
        r'/\*.*?\*/|//[^\n]*|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|[{}]',
        source[opening:], re.S)
    depth = 0
    for token in tokens:
        if token[0] == "{":
            depth += 1
        elif token[0] == "}":
            depth -= 1
            if depth == 0:
                return source[start.start():opening + token.end()]
    raise ValueError(f"unterminated actual source function {name}")


PREFIX = r'''
#include <assert.h>
#include <math.h>
#include <stdint.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
typedef int32_t LONG;
typedef uint32_t DWORD;
typedef uint8_t BYTE;
/* Keep the extracted pointer arithmetic explicitly 32-bit. */
typedef uint32_t ULONG_PTR;
typedef DWORD (*PFN_GetTickCount)(void);
typedef int BOOL;
typedef void* HWND;
typedef struct { LONG x,y; } POINT;
typedef struct { float l,t,r,b; } UIRectF;
#define WINAPI __attribute__((stdcall))
#define TRUE 1
#define FALSE 0
#define PRM_UI_CAPTURE_RVA 0x10UL
#define PRM_UI_MOUSE_RETURN_RVA 0x495BE1UL
#define PRM_TOOLTIP_MANAGER_RVA 0x00A78D8CUL
'''


STUBS = r'''
enum {
    OBJ_CHAT = 0,
    OBJ_BASIC = 1,
    OBJ_MENU = 2,
    OBJ_UNKNOWN = 3,
    OBJ_CHAT_CHILD = 4,
    OBJ_BASIC_CHILD = 5,
    OBJ_MENU_CHILD = 6,
    OBJ_ANON_A = 7,
    OBJ_ANON_B = 8,
    OBJ_BAD_VTABLE = 9,
    OBJ_COUNT = 10
};
enum {
    VT_CHAT = 0,
    VT_BASIC = 1,
    VT_MENU = 2,
    VT_UNKNOWN = 3,
    VT_CHAT_CHILD = 4,
    VT_BASIC_CHILD = 5,
    VT_MENU_CHILD = 6,
    VT_ANON_A = 7,
    VT_ANON_B = 8,
    VT_REUSED = 9,
    VT_COUNT = 10
};

typedef struct {
    void* vt;
    BYTE pad[0x19c8];
} NativeWindow;

/* Character-info popups keep their source root at +19C8.  Keep the fixture
   root objects large enough to exercise that real native field. */
static NativeWindow g_native[OBJ_COUNT];
static void* g_vtables[VT_COUNT][64];
#define FAKE_EXE_SIZE (PRM_TOOLTIP_MANAGER_RVA+0x100UL)
static BYTE g_fake_exe[FAKE_EXE_SIZE];
static BYTE* g_exe;
static DWORD g_exe_size;

static LONG g_native_x[OBJ_COUNT],g_native_y[OBJ_COUNT];
static LONG g_native_w[OBJ_COUNT],g_native_h[OBJ_COUNT];
static int g_return_child[OBJ_COUNT];
static int g_child_index[OBJ_COUNT];
static DWORD g_native_calls[OBJ_COUNT];
static LONG g_native_last_x[OBJ_COUNT],g_native_last_y[OBJ_COUNT];
static void* g_native_last_self[OBJ_COUNT];
static DWORD g_hover;
static void* g_manager;
static int g_manager_order[4];
static unsigned int g_manager_order_count;
static DWORD g_manager_calls;
static void* g_manager_last_self;
static LONG g_manager_last_x,g_manager_last_y;
static int g_nested_enabled,g_nested_active;
static DWORD g_nested_result;
static int g_nested_outer_scope_seen,g_nested_scope_restored;
static DWORD g_fake_caller_rva;
static HWND g_input_hwnd;
static BOOL g_fake_conversion_ok;
static int g_fallback_calls;
static int g_fallback_enabled;
static LONG g_fake_raw_x,g_fake_raw_y;

static OwnerInputRegion g_owner_input_regions[16];
static OwnerCaptureLink g_owner_capture_links[16];
static DWORD g_owner_input_region_count;
static DWORD g_owner_capture_link_count;
static DWORD g_ui_present_serial;
static DWORD g_owner_capture_object,g_owner_capture_root;
static float g_owner_capture_ax,g_owner_capture_ay;
static float g_owner_capture_scale,g_owner_capture_offset_x,g_owner_capture_offset_y;
static int g_owner_capture_native_size;
static DWORD g_owner_capture_maps,g_owner_capture_changes,g_owner_capture_unknown;
static DWORD g_owner_mapped_mouse,g_owner_input_candidates,g_owner_input_overlap_hits;
static int g_owner_input_remap_enabled,g_owner_scale_enabled;
static int g_input_enabled,g_input_runtime_enabled,g_ui_runtime_enabled;
static int g_owner_bitmap_hooks_installed;
static int g_owner_hit_hooks_installed;
static DWORD g_owner_hit_queries,g_owner_hit_scoped,g_owner_hit_rejected;
static DWORD g_owner_hit_unmatched;
static OwnerHitSelection g_owner_hit_selection;
static OwnerHitScope g_owner_hit_scope;
static OwnerTooltipBinding g_owner_tooltip_binding;
static PFN_GetTickCount g_owner_tooltip_clock;
static DWORD g_tooltip_tick;
static void owner_tooltip_publish_refresh(DWORD,DWORD,const OwnerInputRegion*);
static int g_locked;
static float g_scale;
static DWORD g_thread_id;

typedef DWORD (__attribute__((thiscall)) *NativeHitFn)(void*,LONG,LONG);
typedef DWORD (__attribute__((thiscall)) *PFN_UIHit)(void*,LONG,LONG);

static DWORD __attribute__((thiscall)) owner_hit_candidate(void*,LONG,LONG);
static DWORD __attribute__((thiscall)) owner_hit_query_scoped(void*,LONG,LONG);
static int remap_owner_point_selected(POINT*,OwnerHitSelection*);
static void owner_hit_publish(const OwnerHitSelection*);
static PFN_UIHit g_owner_hit_query;

static int range_readable(const void* p, DWORD bytes, const void* base, size_t size) {
    uintptr_t q=(uintptr_t)p,b=(uintptr_t)base;
    if(!p || !bytes || q<b || q>b+size) return 0;
    return (uintptr_t)bytes <= b+size-q;
}
static int mem_readable(const void* p, DWORD bytes) {
    return range_readable(p,bytes,g_native,sizeof(g_native)) ||
           range_readable(p,bytes,g_vtables,sizeof(g_vtables)) ||
           range_readable(p,bytes,g_fake_exe,sizeof(g_fake_exe));
}
static void owner_input_region_lock(void) {
    assert(!g_locked);
    g_locked=1;
}
static void owner_input_region_unlock(void) {
    assert(g_locked);
    g_locked=0;
}
static float ui_scale_factor(void) {
    return g_scale;
}
static DWORD current_thread(void) {
    return g_thread_id;
}
static DWORD (*g_GetCurrentThreadId)(void)=current_thread;

static DWORD ptr_to_rva(void* p) {
    (void)p;
    return g_fake_caller_rva;
}
static void maybe_toggle_ui_input(void) {}
static void maybe_toggle_world_input(void) {}
static void maybe_dump_ui_groups(void) {}
static void maybe_dump_owner_windows(void) {}
static void vtrace_poll_hotkey(void) {}
static int remap_ui_point(POINT* p) {
    if(!p || !g_fallback_enabled) return 0;
    ++g_fallback_calls;
    p->x-=3;
    p->y-=5;
    return 1;
}
static BOOL fake_screen_to_client(HWND hwnd,POINT* p) {
    (void)hwnd;
    assert(p);
    if(!g_fake_conversion_ok) return 0;
    p->x=g_fake_raw_x;
    p->y=g_fake_raw_y;
    return 1;
}
static BOOL (*g_real_ScreenToClient)(HWND,POINT*)=fake_screen_to_client;

static DWORD native_ptr(int index) {
    return (DWORD)(ULONG_PTR)&g_native[index];
}
static DWORD native_vt(int index) {
    return (DWORD)(ULONG_PTR)g_native[index].vt;
}
static int native_index(void* self) {
    int i;
    for(i=0;i<OBJ_COUNT;++i) if(self==&g_native[i]) return i;
    return -1;
}
static DWORD native_hit_common(void* self,LONG x,LONG y) {
    int i=native_index(self);
    if(i<0 || i==OBJ_BAD_VTABLE) return 0;
    ++g_native_calls[i];
    g_native_last_self[i]=self;
    g_native_last_x[i]=x;
    g_native_last_y[i]=y;
    if(x<g_native_x[i] || x>=g_native_x[i]+g_native_w[i] ||
       y<g_native_y[i] || y>=g_native_y[i]+g_native_h[i]) return 0;
    if(g_return_child[i] && g_child_index[i]>=0)
        return native_ptr(g_child_index[i]);
    return native_ptr(i);
}
static DWORD __attribute__((thiscall)) native_chat_hit(void* self,LONG x,LONG y) {
    return native_hit_common(self,x,y);
}
static DWORD __attribute__((thiscall)) native_basic_hit(void* self,LONG x,LONG y) {
    return native_hit_common(self,x,y);
}
static DWORD __attribute__((thiscall)) native_menu_hit(void* self,LONG x,LONG y) {
    return native_hit_common(self,x,y);
}
static DWORD __attribute__((thiscall)) native_unknown_hit(void* self,LONG x,LONG y) {
    return native_hit_common(self,x,y);
}
static DWORD __attribute__((thiscall)) native_child_hit(void* self,LONG x,LONG y) {
    return native_hit_common(self,x,y);
}
static DWORD __attribute__((thiscall)) native_anon_a_hit(void* self,LONG x,LONG y) {
    return native_hit_common(self,x,y);
}
static DWORD __attribute__((thiscall)) native_anon_b_hit(void* self,LONG x,LONG y) {
    return native_hit_common(self,x,y);
}
static DWORD __attribute__((thiscall)) native_reused_hit(void* self,LONG x,LONG y) {
    return native_hit_common(self,x,y);
}

static void native_reset(void) {
    unsigned int i;
    memset(g_native,0,sizeof(g_native));
    memset(g_vtables,0,sizeof(g_vtables));
    for(i=0;i<OBJ_COUNT;++i) g_native[i].vt=g_vtables[i<VT_COUNT?i:VT_CHAT];
    g_native[OBJ_BAD_VTABLE].vt=(void*)(ULONG_PTR)0x12345678UL;
    g_vtables[VT_CHAT][0xb8/4]=(void*)native_chat_hit;
    g_vtables[VT_BASIC][0xb8/4]=(void*)native_basic_hit;
    g_vtables[VT_MENU][0xb8/4]=(void*)native_menu_hit;
    g_vtables[VT_UNKNOWN][0xb8/4]=(void*)native_unknown_hit;
    g_vtables[VT_CHAT_CHILD][0xb8/4]=(void*)native_child_hit;
    g_vtables[VT_BASIC_CHILD][0xb8/4]=(void*)native_child_hit;
    g_vtables[VT_MENU_CHILD][0xb8/4]=(void*)native_child_hit;
    g_vtables[VT_ANON_A][0xb8/4]=(void*)native_anon_a_hit;
    g_vtables[VT_ANON_B][0xb8/4]=(void*)native_anon_b_hit;
    g_vtables[VT_REUSED][0xb8/4]=(void*)native_reused_hit;
    g_native_x[OBJ_CHAT]=0; g_native_y[OBJ_CHAT]=827;
    g_native_w[OBJ_CHAT]=600; g_native_h[OBJ_CHAT]=250;
    g_native_x[OBJ_BASIC]=80; g_native_y[OBJ_BASIC]=902;
    g_native_w[OBJ_BASIC]=220; g_native_h[OBJ_BASIC]=134;
    g_native_x[OBJ_MENU]=80; g_native_y[OBJ_MENU]=902;
    g_native_w[OBJ_MENU]=220; g_native_h[OBJ_MENU]=134;
    g_native_x[OBJ_ANON_A]=400; g_native_y[OBJ_ANON_A]=200;
    g_native_w[OBJ_ANON_A]=160; g_native_h[OBJ_ANON_A]=120;
    g_native_x[OBJ_ANON_B]=400; g_native_y[OBJ_ANON_B]=200;
    g_native_w[OBJ_ANON_B]=160; g_native_h[OBJ_ANON_B]=120;
    g_native_x[OBJ_UNKNOWN]=0; g_native_y[OBJ_UNKNOWN]=827;
    g_native_w[OBJ_UNKNOWN]=600; g_native_h[OBJ_UNKNOWN]=250;
    g_native_x[OBJ_CHAT_CHILD]=0; g_native_y[OBJ_CHAT_CHILD]=827;
    g_native_w[OBJ_CHAT_CHILD]=600; g_native_h[OBJ_CHAT_CHILD]=250;
    g_native_x[OBJ_BASIC_CHILD]=80; g_native_y[OBJ_BASIC_CHILD]=902;
    g_native_w[OBJ_BASIC_CHILD]=220; g_native_h[OBJ_BASIC_CHILD]=134;
    g_native_x[OBJ_MENU_CHILD]=80; g_native_y[OBJ_MENU_CHILD]=902;
    g_native_w[OBJ_MENU_CHILD]=220; g_native_h[OBJ_MENU_CHILD]=134;
    for(i=0;i<OBJ_COUNT;++i) g_child_index[i]=-1;
    g_child_index[OBJ_CHAT]=OBJ_CHAT_CHILD;
    g_child_index[OBJ_BASIC]=OBJ_BASIC_CHILD;
    g_child_index[OBJ_MENU]=OBJ_MENU_CHILD;
}

static DWORD __attribute__((thiscall)) fake_manager_query(void* self,LONG x,LONG y) {
    unsigned int i;
    assert(self==g_manager);
    ++g_manager_calls;
    g_manager_last_self=self;
    g_manager_last_x=x;
    g_manager_last_y=y;
    if(g_nested_enabled && !g_nested_active) {
        g_nested_outer_scope_seen=g_owner_hit_scope.valid;
        g_nested_active=1;
        g_nested_result=owner_hit_query_scoped(self,x+1,y);
        g_nested_active=0;
        g_nested_scope_restored=g_owner_hit_scope.valid;
        g_manager_last_self=self;
        g_manager_last_x=x;
        g_manager_last_y=y;
    }
    g_hover=0;
    for(i=0;i<g_manager_order_count;++i) {
        int index=g_manager_order[i];
        DWORD result=owner_hit_candidate(&g_native[index],x,y);
        if(result) {
            g_hover=result;
            return result;
        }
    }
    return 0;
}

static void source_reset(void) {
    assert(!g_locked);
    memset(g_owner_input_regions,0,sizeof(g_owner_input_regions));
    memset(g_owner_capture_links,0,sizeof(g_owner_capture_links));
    memset(g_fake_exe,0,sizeof(g_fake_exe));
    g_exe=g_fake_exe;
    g_exe_size=sizeof(g_fake_exe);
    /* The native tooltip manager owns the one transient explanation object.
       Actor speech uses the same class but is absent from this slot. */
    *(DWORD*)(g_fake_exe+PRM_TOOLTIP_MANAGER_RVA)=native_ptr(OBJ_UNKNOWN);
    *(DWORD*)((BYTE*)&g_native[OBJ_UNKNOWN]+0x1c)=native_ptr(OBJ_CHAT);
    g_owner_input_region_count=0;
    g_owner_capture_link_count=0;
    g_ui_present_serial=100;
    g_owner_capture_object=0;
    g_owner_capture_root=0;
    g_owner_capture_ax=0;
    g_owner_capture_ay=0;
    g_owner_capture_scale=0;
    g_owner_capture_offset_x=g_owner_capture_offset_y=0;
    g_owner_capture_native_size=0;
    g_owner_capture_maps=0;
    g_owner_capture_changes=0;
    g_owner_capture_unknown=0;
    g_owner_mapped_mouse=0;
    g_owner_input_candidates=0;
    g_owner_input_overlap_hits=0;
    g_owner_input_remap_enabled=1;
    g_owner_scale_enabled=1;
    g_input_enabled=1;
    g_input_runtime_enabled=1;
    g_ui_runtime_enabled=1;
    g_owner_bitmap_hooks_installed=1;
    g_owner_hit_hooks_installed=1;
    g_owner_hit_queries=0;
    g_owner_hit_scoped=0;
    g_owner_hit_rejected=0;
    g_owner_hit_unmatched=0;
    memset(&g_owner_hit_selection,0,sizeof(g_owner_hit_selection));
    memset(&g_owner_hit_scope,0,sizeof(g_owner_hit_scope));
    memset(&g_owner_tooltip_binding,0,sizeof(g_owner_tooltip_binding));
    (void)g_owner_tooltip_clock;
    g_tooltip_tick=700;
    *(DWORD*)((BYTE*)&g_native[OBJ_UNKNOWN]+0x20)=g_tooltip_tick;
    *(DWORD*)(g_fake_exe+PRM_UI_CAPTURE_RVA)=0;
    g_locked=0;
    g_scale=2.0f;
    g_thread_id=17;
    g_manager_order[0]=OBJ_CHAT;
    g_manager_order[1]=OBJ_BASIC;
    g_manager_order_count=2;
    g_manager_calls=0;
    g_manager_last_self=0;
    g_manager_last_x=g_manager_last_y=0;
    g_hover=0;
    g_nested_enabled=0;
    g_nested_active=0;
    g_nested_result=0;
    g_nested_outer_scope_seen=0;
    g_nested_scope_restored=0;
    g_fake_caller_rva=PRM_UI_MOUSE_RETURN_RVA;
    g_input_hwnd=0;
    g_fake_conversion_ok=1;
    g_fallback_calls=0;
    g_fallback_enabled=1;
    g_fake_raw_x=0;
    g_fake_raw_y=0;
    g_real_ScreenToClient=fake_screen_to_client;
    memset(g_native_calls,0,sizeof(g_native_calls));
    memset(g_native_last_x,0,sizeof(g_native_last_x));
    memset(g_native_last_y,0,sizeof(g_native_last_y));
    memset(g_native_last_self,0,sizeof(g_native_last_self));
    memset(g_return_child,0,sizeof(g_return_child));
    g_manager=(void*)&g_native[OBJ_MENU_CHILD];
    g_owner_hit_query=fake_manager_query;
}

static void reset_all(void) {
    native_reset();
    source_reset();
}

static void add_region(unsigned int index,int object,DWORD present,
                       float l,float t,float r,float b,float ax,float ay,
                       DWORD input_order,DWORD exact_order,int native_size) {
    OwnerInputRegion* m=&g_owner_input_regions[index];
    memset(m,0,sizeof(*m));
    m->rect=(UIRectF){l,t,r,b};
    m->ax=ax;
    m->ay=ay;
    m->fit_scale=g_scale;
    m->offset_x=m->offset_y=0;
    m->object_ptr=native_ptr(object);
    m->present=present;
    m->input_order=input_order;
    m->exact_order=exact_order;
    m->vtable_ptr=native_vt(object);
    m->native_size=native_size;
    if(g_owner_input_region_count<=index) g_owner_input_region_count=index+1;
}

static void add_logcase(void) {
    add_region(0,OBJ_CHAT,g_ui_present_serial,0,827,600,1077,0,720,10,10,0);
    add_region(1,OBJ_BASIC,g_ui_present_serial,80,902,300,1036,0,1440,20,20,0);
}
static void add_overlap(DWORD chat_exact,DWORD basic_exact) {
    add_region(0,OBJ_CHAT,g_ui_present_serial,80,902,300,1036,0,1440,10,chat_exact,0);
    add_region(1,OBJ_BASIC,g_ui_present_serial,80,902,300,1036,0,1440,20,basic_exact,0);
}
static void publish_remap(POINT* p,OwnerHitSelection* hit) {
    assert(remap_owner_point_selected(p,hit));
    assert(hit->valid);
    owner_hit_publish(hit);
}
static void refresh_tooltip(const OwnerHitSelection* hit) {
    owner_tooltip_publish_refresh(native_ptr(OBJ_UNKNOWN),g_tooltip_tick,
                                  hit && hit->valid?&hit->region:0);
    *(DWORD*)((BYTE*)&g_native[OBJ_UNKNOWN]+0x20)=g_tooltip_tick;
}
static DWORD query_at(LONG x,LONG y) {
    return owner_hit_query_scoped(g_manager,x,y);
}
static void expect_point(POINT p,LONG x,LONG y) {
    assert(p.x==x && p.y==y);
}
static void expect_unscoped_chat(DWORD expected_unmatched) {
    DWORD result=query_at(150,945);
    assert(result==native_ptr(OBJ_CHAT));
    assert(g_hover==result);
    assert(g_owner_hit_scoped==0);
    assert(g_owner_hit_unmatched==expected_unmatched);
    assert(g_native_calls[OBJ_CHAT]==1);
    assert(g_native_last_x[OBJ_CHAT]==150 && g_native_last_y[OBJ_CHAT]==945);
}
'''


TESTS = r'''
static void popup_class(OwnerWindowState* st,const char* name) {
    memset(st,0,sizeof(*st));
    st->object_ptr=native_ptr(OBJ_CHAT);
    strcpy(st->class_name,name);
}
static void expect_popup_offset(float dx,float dy,float want_x,float want_y) {
    assert(fabsf(dx-want_x)<0.001f && fabsf(dy-want_y)<0.001f);
}
static void test_popup_offset_uses_fresh_selected_owner(void) {
    OwnerWindowState st; OwnerHitSelection before; POINT p; float dx,dy;

    /* The selected hit is a displayed 200% owner.  The popup origin is in
       that owner's native/source coordinates, so the same transform must be
       applied to it. */
    reset_all();
    add_region(0,OBJ_BASIC,g_ui_present_serial,80,902,300,1036,0,1440,20,20,0);
    p=(POINT){300,450}; publish_remap(&p,&before);
    refresh_tooltip(&before);
    popup_class(&st,"UITransBalloonText");
    dx=7.0f; dy=-9.0f;
    owner_popup_offset(&st,250,900,&dx,&dy);
    expect_popup_offset(dx,dy,250.0f,-540.0f);
    assert(memcmp(&before,&g_owner_hit_selection,sizeof(before))==0);

    /* A moved owner with a new scale and translation is selected from the
       fresh region while the sample itself remains stationary. */
    reset_all();
    g_scale=1.5f;
    add_region(0,OBJ_BASIC,g_ui_present_serial,80,902,300,1036,100,1200,20,20,0);
    g_owner_input_regions[0].offset_x=11.0f;
    g_owner_input_regions[0].offset_y=-13.0f;
    p=(POINT){250,800}; publish_remap(&p,&before);
    popup_class(&st,"UICharInfoBalloonText");
    g_ui_present_serial=101;
    memset(g_owner_input_regions,0,sizeof(g_owner_input_regions));
    g_owner_input_region_count=0;
    add_region(0,OBJ_BASIC,g_ui_present_serial,80,902,300,1036,40,1380,20,20,0);
    g_owner_input_regions[0].offset_x=6.0f;
    g_owner_input_regions[0].offset_y=-8.0f;
    *(DWORD*)((BYTE*)&g_native[OBJ_BASIC]+0x19c8)=st.object_ptr;
    /* Keep the old hit publication and prove the helper revalidates it
       against the current region without publishing a new selection. */
    {
        OwnerHitSelection stationary=before;
        dx=5.0f; dy=6.0f;
        owner_popup_offset(&st,250,900,&dx,&dy);
        expect_popup_offset(dx,dy,111.0f,-248.0f);
        assert(memcmp(&stationary,&g_owner_hit_selection,sizeof(stationary))==0);
    }
}

static void test_popup_offset_bypasses_stale_or_unmatched_sources(void) {
    OwnerWindowState st; OwnerHitSelection hit; POINT p; float dx,dy;

    reset_all();
    add_region(0,OBJ_BASIC,g_ui_present_serial,80,902,300,1036,0,1440,20,20,0);
    p=(POINT){300,450}; publish_remap(&p,&hit);
    popup_class(&st,"UITransBalloonText");
    /* Actor speech shares UITransBalloonText but is not the controller's
       explanation instance, so a hovered UI owner cannot move it. */
    *(DWORD*)((BYTE*)&g_native[OBJ_UNKNOWN]+0x1c)=native_ptr(OBJ_MENU);
    dx=7.0f; dy=-9.0f;
    owner_popup_offset(&st,250,900,&dx,&dy);
    assert(dx==7.0f && dy==-9.0f);

    reset_all();
    add_region(0,OBJ_BASIC,g_ui_present_serial,80,902,300,1036,0,1440,20,20,0);
    p=(POINT){300,450}; publish_remap(&p,&hit);
    popup_class(&st,"UITransBalloonText");
    g_ui_present_serial+=3;
    dx=7.0f; dy=-9.0f;
    owner_popup_offset(&st,250,900,&dx,&dy);
    assert(dx==7.0f && dy==-9.0f);

    reset_all();
    add_region(0,OBJ_BASIC,g_ui_present_serial,80,902,300,1036,0,1440,20,20,0);
    p=(POINT){300,450}; publish_remap(&p,&hit);
    g_owner_input_regions[0].object_ptr=native_ptr(OBJ_CHAT);
    g_owner_input_regions[0].vtable_ptr=native_vt(OBJ_CHAT);
    dx=-4.0f; dy=12.0f;
    owner_popup_offset(&st,250,900,&dx,&dy);
    assert(dx==-4.0f && dy==12.0f);

    reset_all();
    add_region(0,OBJ_BASIC,g_ui_present_serial,80,902,300,1036,0,1440,20,20,1);
    p=(POINT){100,950}; publish_remap(&p,&hit);
    dx=13.0f; dy=-2.0f;
    owner_popup_offset(&st,250,900,&dx,&dy);
    assert(dx==13.0f && dy==-2.0f);

    reset_all();
    add_region(0,OBJ_BASIC,g_ui_present_serial,80,902,300,1036,0,1440,20,20,0);
    p=(POINT){300,450}; publish_remap(&p,&hit);
    popup_class(&st,"UICharInfoBalloonText");
    *(DWORD*)((BYTE*)&g_native[OBJ_BASIC]+0x19c8)=native_ptr(OBJ_MENU);
    dx=-15.0f; dy=4.0f;
    owner_popup_offset(&st,250,900,&dx,&dy);
    assert(dx==-15.0f && dy==4.0f);

    *(DWORD*)((BYTE*)&g_native[OBJ_BASIC]+0x19c8)=st.object_ptr;
    g_native[OBJ_BASIC].vt=g_vtables[VT_REUSED];
    owner_popup_offset(&st,250,900,&dx,&dy);
    assert(dx==-15.0f && dy==4.0f);

    reset_all();
    add_region(0,OBJ_BASIC,g_ui_present_serial,80,902,300,1036,0,1440,20,20,0);
    p=(POINT){300,450}; publish_remap(&p,&hit);
    popup_class(&st,"UITransBalloonTextOther");
    dx=19.0f; dy=23.0f;
    owner_popup_offset(&st,250,900,&dx,&dy);
    assert(dx==19.0f && dy==23.0f);
    puts("PASS: popup offsets require exact class, fresh matching selected owner, and non-native-size source; selection remains passive");
}

static void test_logcase_basic_filters_chat(void) {
    POINT p={300,450}; OwnerHitSelection hit={0},published;
    NativeWindow before_object; void* before_vt_entry;
    reset_all(); add_logcase();
    publish_remap(&p,&hit);
    expect_point(p,150,945);
    assert(hit.region.object_ptr==native_ptr(OBJ_BASIC));
    assert(hit.region.vtable_ptr==native_vt(OBJ_BASIC));
    assert(hit.raw.x==300 && hit.raw.y==450);
    assert(hit.mapped.x==150 && hit.mapped.y==945);
    assert(hit.thread==17);
    published=hit;
    owner_hit_publish(&hit);
    hit.raw.x=9999; hit.mapped.y=9999;
    assert(g_owner_hit_selection.raw.x==300);
    assert(g_owner_hit_selection.mapped.y==945);
    g_owner_input_regions[1].rect.l=4000;
    assert(g_owner_hit_selection.region.object_ptr==published.region.object_ptr);
    assert(g_owner_hit_selection.region.vtable_ptr==published.region.vtable_ptr);
    g_owner_input_regions[1].rect.l=80;
    before_object=g_native[OBJ_BASIC];
    before_vt_entry=g_vtables[VT_BASIC][0xb8/4];
    g_return_child[OBJ_BASIC]=1;
    {
        DWORD result=query_at(150,945);
        assert(result==native_ptr(OBJ_BASIC_CHILD));
        assert(g_hover==result);
    }
    assert(g_owner_hit_queries==1 && g_owner_hit_scoped==1);
    assert(g_owner_hit_unmatched==0 && g_owner_hit_rejected==1);
    assert(g_native_calls[OBJ_CHAT]==0);
    assert(g_native_calls[OBJ_BASIC]==1);
    assert(g_native_last_self[OBJ_BASIC]==&g_native[OBJ_BASIC]);
    assert(g_native_last_x[OBJ_BASIC]==150 && g_native_last_y[OBJ_BASIC]==945);
    assert(g_manager_last_self==g_manager && g_manager_last_x==150 && g_manager_last_y==945);
    assert(!g_owner_hit_scope.valid);
    assert(memcmp(&before_object,&g_native[OBJ_BASIC],sizeof(before_object))==0);
    assert(g_vtables[VT_BASIC][0xb8/4]==before_vt_entry);
    puts("PASS: 200% Basic visual target remaps 300,450 to 150,945, rejects native Chat, preserves child result/args, and writes no native data");
}

static void test_real_visual_chat_and_native_size(void) {
    POINT p={150,945}; OwnerHitSelection hit={0};
    reset_all();
    add_region(0,OBJ_CHAT,g_ui_present_serial,0,827,600,1077,0,720,30,30,1);
    g_return_child[OBJ_CHAT]=1;
    publish_remap(&p,&hit);
    expect_point(p,150,945);
    assert(hit.region.object_ptr==native_ptr(OBJ_CHAT));
    assert(hit.region.native_size==1);
    {
        DWORD result=query_at(150,945);
        assert(result==native_ptr(OBJ_CHAT_CHILD));
    }
    assert(g_owner_hit_scoped==1 && g_owner_hit_rejected==0);
    assert(g_native_calls[OBJ_CHAT]==1);
    assert(g_native_last_x[OBJ_CHAT]==150 && g_native_last_y[OBJ_CHAT]==945);
    puts("PASS: a native-size Chat visual remains interactive at its real rectangle and is not filtered by the scaled-owner path");
}

static void test_menu_overlap_uses_its_own_vtable(void) {
    POINT p={300,450}; OwnerHitSelection hit={0};
    void* menu_entry;
    reset_all();
    add_region(0,OBJ_CHAT,g_ui_present_serial,80,902,300,1036,0,1440,10,10,0);
    add_region(1,OBJ_BASIC,g_ui_present_serial,80,902,300,1036,0,1440,20,20,0);
    add_region(2,OBJ_MENU,g_ui_present_serial,80,902,300,1036,0,1440,30,30,0);
    g_manager_order[0]=OBJ_CHAT; g_manager_order[1]=OBJ_MENU;
    g_manager_order[2]=OBJ_BASIC; g_manager_order_count=3;
    g_return_child[OBJ_MENU]=1;
    menu_entry=g_vtables[VT_MENU][0xb8/4];
    publish_remap(&p,&hit);
    expect_point(p,150,945);
    assert(hit.region.object_ptr==native_ptr(OBJ_MENU));
    {
        DWORD result=query_at(150,945);
        assert(result==native_ptr(OBJ_MENU_CHILD));
    }
    assert(g_native_calls[OBJ_CHAT]==0 && g_native_calls[OBJ_BASIC]==0);
    assert(g_native_calls[OBJ_MENU]==1);
    assert(g_native_last_x[OBJ_MENU]==150 && g_native_last_y[OBJ_MENU]==945);
    assert(g_owner_hit_rejected==1);
    assert(g_vtables[VT_MENU][0xb8/4]==menu_entry);
    puts("PASS: menu-overlap selection rejects only other copied owners and dispatches through the menu vtable slot");
}

static void test_topmost_visual_overlap(void) {
    POINT p; OwnerHitSelection hit;
    DWORD result;
    reset_all(); add_overlap(10,20);
    p=(POINT){300,450}; publish_remap(&p,&hit);
    assert(hit.region.object_ptr==native_ptr(OBJ_BASIC));
    result=query_at(150,945);
    assert(result==native_ptr(OBJ_BASIC));
    assert(g_native_calls[OBJ_CHAT]==0 && g_native_calls[OBJ_BASIC]==1);
    assert(g_owner_hit_rejected==1);

    reset_all(); add_overlap(30,20);
    p=(POINT){300,450}; publish_remap(&p,&hit);
    assert(hit.region.object_ptr==native_ptr(OBJ_CHAT));
    result=query_at(150,945);
    assert(result==native_ptr(OBJ_CHAT));
    assert(g_native_calls[OBJ_CHAT]==1 && g_native_calls[OBJ_BASIC]==0);
    assert(g_owner_hit_rejected==0);
    puts("PASS: exact visual order wins overlapping regions in both directions while native manager order stays Chat then Basic");
}

static void test_stale_and_reused_snapshot_vtables(void) {
    POINT p; OwnerHitSelection hit;
    DWORD result;
    reset_all(); add_logcase(); p=(POINT){300,450}; publish_remap(&p,&hit);
    g_native[OBJ_BASIC].vt=g_vtables[VT_REUSED];
    result=query_at(150,945);
    assert(result==native_ptr(OBJ_CHAT));
    assert(g_owner_hit_scoped==0 && g_owner_hit_unmatched==1);
    assert(g_owner_hit_rejected==0);

    reset_all(); add_logcase(); p=(POINT){300,450}; publish_remap(&p,&hit);
    g_owner_input_regions[1].vtable_ptr=(DWORD)(ULONG_PTR)g_vtables[VT_REUSED];
    g_native[OBJ_BASIC].vt=g_vtables[VT_REUSED];
    result=query_at(150,945);
    assert(result==native_ptr(OBJ_CHAT));
    assert(g_owner_hit_scoped==0 && g_owner_hit_unmatched==1);

    reset_all(); add_logcase(); p=(POINT){300,450}; publish_remap(&p,&hit);
    g_ui_present_serial+=3;
    result=query_at(150,945);
    assert(result==native_ptr(OBJ_CHAT));
    assert(g_owner_hit_scoped==0 && g_owner_hit_unmatched==1);
    puts("PASS: changed live vtables, reused snapshot vtables, and over-age stationary snapshots disable filtering and preserve native Chat");
}

static void test_thread_and_coordinate_mismatch(void) {
    POINT p; OwnerHitSelection hit;
    DWORD result;
    reset_all(); add_logcase(); p=(POINT){300,450}; publish_remap(&p,&hit);
    g_thread_id=18;
    result=query_at(150,945);
    assert(result==native_ptr(OBJ_CHAT));
    assert(g_owner_hit_scoped==0 && g_owner_hit_unmatched==1);

    reset_all(); add_logcase(); p=(POINT){300,450}; publish_remap(&p,&hit);
    result=query_at(151,945);
    assert(result==native_ptr(OBJ_CHAT));
    assert(g_owner_hit_scoped==0 && g_owner_hit_unmatched==1);
    assert(g_native_calls[OBJ_CHAT]==1 && g_native_calls[OBJ_BASIC]==0);
    puts("PASS: thread and mapped-coordinate mismatches leave native query arguments and Chat hover untouched");
}

static void test_stationary_reuse_with_fresh_regions(void) {
    POINT p={300,450}; OwnerHitSelection hit={0};
    unsigned int i;
    reset_all(); add_logcase(); publish_remap(&p,&hit);
    g_return_child[OBJ_BASIC]=1;
    for(i=0;i<32;++i) {
        DWORD result;
        g_ui_present_serial=200+i;
        memset(g_owner_input_regions,0,sizeof(g_owner_input_regions));
        g_owner_input_region_count=0;
        add_logcase();
        result=query_at(150,945);
        assert(result==native_ptr(OBJ_BASIC_CHILD));
        assert(g_owner_hit_scope.valid==0);
    }
    assert(g_owner_hit_queries==32 && g_owner_hit_scoped==32);
    assert(g_owner_hit_unmatched==0 && g_owner_hit_rejected==32);
    assert(g_native_calls[OBJ_CHAT]==0 && g_native_calls[OBJ_BASIC]==32);
    assert(g_native_last_x[OBJ_BASIC]==150 && g_native_last_y[OBJ_BASIC]==945);
    puts("PASS: one stationary raw sample is reused across 32 fresh presents with copied regions and fresh scoped validation");
}

static void test_capture_disabled_noowner_and_unknown_passthrough(void) {
    static int* const gates[]={
        &g_owner_input_remap_enabled,&g_owner_scale_enabled,&g_input_enabled,
        &g_input_runtime_enabled,&g_ui_runtime_enabled
    };
    unsigned int i;
    POINT p; OwnerHitSelection hit; DWORD result;

    reset_all(); add_logcase(); p=(POINT){300,700}; hit=(OwnerHitSelection){0};
    assert(!remap_owner_point_selected(&p,&hit));
    expect_point(p,300,700); assert(!hit.valid);
    owner_hit_publish(&hit);
    expect_unscoped_chat(1);

    for(i=0;i<sizeof(gates)/sizeof(gates[0]);++i) {
        reset_all(); add_logcase(); p=(POINT){300,450}; hit=(OwnerHitSelection){0};
        *gates[i]=0;
        assert(!remap_owner_point_selected(&p,&hit));
        expect_point(p,300,450); assert(!hit.valid);
        owner_hit_publish(&hit);
        expect_unscoped_chat(1);
    }

    reset_all(); add_logcase(); p=(POINT){300,450}; hit=(OwnerHitSelection){0};
    *(DWORD*)(g_fake_exe+PRM_UI_CAPTURE_RVA)=native_ptr(OBJ_BASIC);
    assert(remap_owner_point_selected(&p,&hit));
    expect_point(p,150,945);
    assert(!hit.valid);
    owner_hit_publish(&hit);
    expect_unscoped_chat(1);
    *(DWORD*)(g_fake_exe+PRM_UI_CAPTURE_RVA)=0;

    reset_all(); add_logcase(); p=(POINT){300,450}; publish_remap(&p,&hit);
    g_manager_order[0]=OBJ_UNKNOWN; g_manager_order[1]=OBJ_CHAT;
    g_manager_order[2]=OBJ_BASIC; g_manager_order_count=3;
    result=query_at(150,945);
    assert(result==native_ptr(OBJ_UNKNOWN));
    assert(g_hover==result && g_native_calls[OBJ_UNKNOWN]==1);
    assert(g_native_last_x[OBJ_UNKNOWN]==150 && g_native_last_y[OBJ_UNKNOWN]==945);
    assert(g_native_calls[OBJ_CHAT]==0 && g_native_calls[OBJ_BASIC]==0);
    assert(g_owner_hit_scoped==1 && g_owner_hit_rejected==0);

    assert(owner_hit_candidate(0,150,945)==0);
    assert(owner_hit_candidate(&g_native[OBJ_BAD_VTABLE],150,945)==0);
    puts("PASS: no-owner, every disable gate, native capture, unknown candidates, null, and unreadable vtables all preserve passthrough");
}

static void test_nested_scope_and_forwarding(void) {
    POINT p={300,450}; OwnerHitSelection hit={0};
    NativeWindow before_chat,before_basic;
    DWORD result;
    reset_all(); add_logcase(); publish_remap(&p,&hit);
    before_chat=g_native[OBJ_CHAT]; before_basic=g_native[OBJ_BASIC];
    g_nested_enabled=1;
    result=query_at(150,945);
    assert(result==native_ptr(OBJ_BASIC));
    assert(g_nested_result==native_ptr(OBJ_CHAT));
    assert(g_nested_outer_scope_seen==1 && g_nested_scope_restored==1);
    assert(g_manager_calls==2);
    assert(g_manager_last_self==g_manager);
    assert(g_manager_last_x==150 && g_manager_last_y==945);
    assert(g_owner_hit_scoped==1 && g_owner_hit_unmatched==1);
    assert(g_owner_hit_rejected==1);
    assert(g_native_calls[OBJ_CHAT]==1 && g_native_calls[OBJ_BASIC]==1);
    assert(g_native_last_x[OBJ_CHAT]==151 && g_native_last_y[OBJ_CHAT]==945);
    assert(g_native_last_x[OBJ_BASIC]==150 && g_native_last_y[OBJ_BASIC]==945);
    assert(!g_owner_hit_scope.valid);
    assert(memcmp(&before_chat,&g_native[OBJ_CHAT],sizeof(before_chat))==0);
    assert(memcmp(&before_basic,&g_native[OBJ_BASIC],sizeof(before_basic))==0);
    puts("PASS: nested original queries restore the outer scope; thiscall self/coordinates/results forward and native objects remain unchanged");
}

static void test_screen_to_client_publication_boundary(void) {
    POINT p;
    OwnerHitSelection published;
    HWND primary=(HWND)&g_native[OBJ_BASIC];
    HWND secondary=(HWND)&g_native[OBJ_CHAT];

    reset_all(); add_logcase();
    g_fake_raw_x=300; g_fake_raw_y=450;
    p=(POINT){1,2};
    assert(hook_ScreenToClient(primary,&p));
    expect_point(p,150,945);
    assert(g_input_hwnd==primary);
    assert(g_fallback_calls==0);
    assert(g_owner_hit_selection.valid);
    assert(g_owner_hit_selection.region.object_ptr==native_ptr(OBJ_BASIC));
    assert(g_owner_hit_selection.raw.x==300 && g_owner_hit_selection.raw.y==450);
    assert(g_owner_hit_selection.mapped.x==150 && g_owner_hit_selection.mapped.y==945);
    published=g_owner_hit_selection;

    g_fake_caller_rva=0;
    g_fake_raw_x=300; g_fake_raw_y=450;
    p=(POINT){7,8};
    assert(hook_ScreenToClient(secondary,&p));
    expect_point(p,150,945);
    assert(g_input_hwnd==primary);
    assert(g_owner_hit_selection.valid);
    assert(g_owner_hit_selection.region.object_ptr==published.region.object_ptr);
    assert(g_owner_hit_selection.region.vtable_ptr==published.region.vtable_ptr);
    assert(g_owner_hit_selection.raw.x==published.raw.x &&
           g_owner_hit_selection.raw.y==published.raw.y);
    assert(g_owner_hit_selection.mapped.x==published.mapped.x &&
           g_owner_hit_selection.mapped.y==published.mapped.y);

    g_fake_caller_rva=PRM_UI_MOUSE_RETURN_RVA;
    g_fake_conversion_ok=0;
    p=(POINT){123,456};
    assert(!hook_ScreenToClient(primary,&p));
    expect_point(p,123,456);
    assert(!g_owner_hit_selection.valid);

    reset_all(); add_logcase();
    g_fake_raw_x=300; g_fake_raw_y=700;
    p=(POINT){9,10};
    assert(hook_ScreenToClient(primary,&p));
    expect_point(p,297,695);
    assert(g_fallback_calls==1);
    assert(g_owner_hit_selection.valid && !g_owner_hit_selection.region.object_ptr);
    assert(g_owner_hit_selection.raw.x==300 && g_owner_hit_selection.raw.y==700);
    expect_unscoped_chat(1);

    reset_all(); add_logcase();
    p=(POINT){123,456};
    g_real_ScreenToClient=0;
    assert(!hook_ScreenToClient(primary,&p));
    expect_point(p,123,456);
    assert(!g_owner_hit_selection.valid);
    puts("PASS: primary ScreenToClient publishes hits or misses, secondary calls preserve them, and failed samples clear them");
}

static void test_display_miss_rejects_ghost_hover(void) {
    POINT p={0,0}; DWORD result;
    reset_all(); add_logcase(); g_fallback_enabled=0;
    g_fake_raw_x=100; g_fake_raw_y=850;
    /* This point is inside native Chat, but outside both displayed windows. */
    assert(fake_manager_query(g_manager,100,850)==native_ptr(OBJ_CHAT));
    memset(g_native_calls,0,sizeof(g_native_calls));
    assert(hook_ScreenToClient((HWND)&g_native[OBJ_BASIC],&p));
    expect_point(p,100,850);
    assert(g_owner_hit_selection.valid && !g_owner_hit_selection.region.object_ptr);
    result=query_at(p.x,p.y);
    assert(result==0 && g_hover==0);
    assert(g_owner_hit_scoped==1 && g_owner_hit_rejected==2);
    assert(!g_native_calls[OBJ_CHAT] && !g_native_calls[OBJ_BASIC]);
    /* A stationary miss stays a miss with freshly published regions. */
    g_ui_present_serial+=50; add_logcase();
    assert(query_at(p.x,p.y)==0);
    /* Unowned native windows retain their own hover/click path. */
    g_manager_order[0]=OBJ_UNKNOWN; g_manager_order_count=1;
    g_native_x[OBJ_UNKNOWN]=0; g_native_y[OBJ_UNKNOWN]=800;
    g_native_w[OBJ_UNKNOWN]=600; g_native_h[OBJ_UNKNOWN]=300;
    assert(query_at(p.x,p.y)==native_ptr(OBJ_UNKNOWN));
    puts("PASS: displayed UI misses reject ghost hover at original rectangles, persist while stationary, and preserve unknown native windows");
}

static void test_anonymous_owner_pairs_and_scale_properties(void) {
    const float scales[]={1.25f,1.33f,1.5f,1.75f,2.0f};
    unsigned int i;
    for(i=0;i<sizeof(scales)/sizeof(scales[0]);++i) {
        POINT p; OwnerHitSelection hit; LONG expected_x,expected_y;
        DWORD result;
        reset_all();
        g_scale=scales[i];
        add_region(0,OBJ_ANON_A,g_ui_present_serial,400,200,560,320,
                   0,0,10,20,0);
        add_region(1,OBJ_ANON_B,g_ui_present_serial,400,200,560,320,
                   0,0,20,10,0);
        /* Feed the manager in the opposite order from the visual winner. */
        g_manager_order[0]=OBJ_ANON_B;
        g_manager_order[1]=OBJ_ANON_A;
        g_manager_order_count=2;
        expected_x=(LONG)((float)450*scales[i]+0.5f);
        expected_y=(LONG)((float)250*scales[i]+0.5f);
        p=(POINT){expected_x,expected_y};
        publish_remap(&p,&hit);
        assert(hit.region.object_ptr==native_ptr(OBJ_ANON_A));
        expect_point(p,450,250);
        result=query_at(450,250);
        assert(result==native_ptr(OBJ_ANON_A));
        assert(g_native_calls[OBJ_ANON_B]==0);
        assert(g_native_calls[OBJ_ANON_A]==1);
        assert(g_native_last_self[OBJ_ANON_A]==&g_native[OBJ_ANON_A]);
        assert(g_native_last_x[OBJ_ANON_A]==450 && g_native_last_y[OBJ_ANON_A]==250);
        assert(g_owner_hit_rejected==1);

        reset_all();
        g_scale=scales[i];
        add_region(0,OBJ_ANON_A,g_ui_present_serial,400,200,560,320,
                   0,0,10,20,0);
        add_region(1,OBJ_ANON_B,g_ui_present_serial,400,200,560,320,
                   0,0,20,30,0);
        /* Swap both the visual winner and native traversal order. */
        g_manager_order[0]=OBJ_ANON_A;
        g_manager_order[1]=OBJ_ANON_B;
        g_manager_order_count=2;
        p=(POINT){expected_x,expected_y};
        publish_remap(&p,&hit);
        assert(hit.region.object_ptr==native_ptr(OBJ_ANON_B));
        expect_point(p,450,250);
        result=query_at(450,250);
        assert(result==native_ptr(OBJ_ANON_B));
        assert(g_native_calls[OBJ_ANON_A]==0);
        assert(g_native_calls[OBJ_ANON_B]==1);
        assert(g_native_last_self[OBJ_ANON_B]==&g_native[OBJ_ANON_B]);
        assert(g_native_last_x[OBJ_ANON_B]==450 && g_native_last_y[OBJ_ANON_B]==250);
        assert(g_owner_hit_rejected==1);
    }
    puts("PASS: anonymous class-free owner pairs survive five scales and both native traversal orders through copied identity/vtable properties");
}

static void test_wrapper_and_direct_candidate_forwarding(void) {
    POINT p={300,450};
    DWORD result;
    reset_all(); add_logcase();
    assert(remap_owner_point(&p));
    expect_point(p,150,945);

    reset_all();
    g_native_x[OBJ_UNKNOWN]=0; g_native_y[OBJ_UNKNOWN]=827;
    g_native_w[OBJ_UNKNOWN]=600; g_native_h[OBJ_UNKNOWN]=250;
    result=owner_hit_candidate(&g_native[OBJ_UNKNOWN],700,944);
    assert(result==0);
    result=owner_hit_candidate(&g_native[OBJ_UNKNOWN],150,945);
    assert(result==native_ptr(OBJ_UNKNOWN));
    assert(g_native_calls[OBJ_UNKNOWN]==2);
    assert(g_native_last_self[OBJ_UNKNOWN]==&g_native[OBJ_UNKNOWN]);
    assert(g_native_last_x[OBJ_UNKNOWN]==150 && g_native_last_y[OBJ_UNKNOWN]==945);
    puts("PASS: the public remap wrapper delegates to selected remapping and direct candidate calls preserve vtable callback forwarding");
}

int main(void) {
    g_manager=(void*)&g_native[OBJ_MENU_CHILD];
    test_popup_offset_uses_fresh_selected_owner();
    test_popup_offset_bypasses_stale_or_unmatched_sources();
    test_logcase_basic_filters_chat();
    test_real_visual_chat_and_native_size();
    test_menu_overlap_uses_its_own_vtable();
    test_topmost_visual_overlap();
    test_stale_and_reused_snapshot_vtables();
    test_thread_and_coordinate_mismatch();
    test_stationary_reuse_with_fresh_regions();
    test_capture_disabled_noowner_and_unknown_passthrough();
    test_nested_scope_and_forwarding();
    test_screen_to_client_publication_boundary();
    test_display_miss_rejects_ghost_hover();
    test_anonymous_owner_pairs_and_scale_properties();
    test_wrapper_and_direct_candidate_forwarding();
    return 0;
}
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path,
                        default=Path(__file__).resolve().with_name("prm_uifix.c"))
    args = parser.parse_args()
    source = args.source.read_text()
    types = "\n".join(extract_type(source, name) for name in (
        "OwnerWindowState", "OwnerInputRegion", "OwnerHitSelection", "OwnerHitScope", "OwnerCaptureLink",
        "OwnerTooltipBinding"))
    ordinary = (
        "s_equal", "rect_contains_point", "rect_area", "owner_native_capture",
        "owner_input_region_bounds", "owner_input_map_region",
        "owner_input_map_capture", "owner_input_select_region", "owner_is_transient_tooltip",
        "owner_tooltip_controller_is_current", "owner_tooltip_publish_refresh", "owner_popup_offset",
        "remap_owner_point_selected", "remap_owner_point", "owner_hit_publish",
        "owner_hit_prepare_scope", "owner_hit_reject_candidate")
    functions = "\n".join(
        extract_definition(source, name) if name in ("owner_input_select_region", "owner_native_capture")
        else extract_function(source, name)
        for name in ordinary)
    functions += "\n" + extract_function_keep_callconv(source, "owner_hit_query_scoped")
    functions += "\n" + extract_function_keep_callconv(source, "owner_hit_candidate")
    functions += "\n" + extract_function_keep_callconv(source, "hook_ScreenToClient")
    code = PREFIX + types + STUBS + functions + TESTS
    with tempfile.TemporaryDirectory(prefix="prm-hit-test-") as directory:
        harness = Path(directory) / "hit.c"
        binary = Path(directory) / "hit-test"
        harness.write_text(code)
        compiler = shlex.split(os.environ.get("CC", "clang"))
        flags = [
            "-m32", "-std=c11", "-O1", "-g", "-Wall", "-Wextra", "-Werror",
            "-fsanitize=address,undefined", "-fno-sanitize-recover=all",
            "-fno-omit-frame-pointer", str(harness), "-o", str(binary),
        ]
        subprocess.run(compiler + flags, check=True)
        env = os.environ.copy()
        env.setdefault("ASAN_OPTIONS", "detect_leaks=0")
        subprocess.run([str(binary)], check=True, env=env)
    print("PASS: extracted owner-hit functions with 32-bit ASan/UBSan native manager fixtures")


if __name__ == "__main__":
    main()
