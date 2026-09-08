#!/usr/bin/env python3
"""Exercise the production per-window hover/update bridge.

The fixture models the manager's no-argument ``vtable+0x40`` dispatch with
real 32-bit ``thiscall`` callbacks.  It keeps the copied visual regions and
the native mouse block in separate storage, so the test catches both a
double inverse-map and a wrapper that leaks its temporary sentinel.
"""

from pathlib import Path
import os
import re
import shlex
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parent


def extract_function(source, name):
    """Extract an actual function definition, preserving call attributes."""
    candidates = re.finditer(
        r"^(?:static\s+|DWORD\s+WINAPI\s+)[^\n]*\b" +
        re.escape(name) + r"\s*\(", source, re.M
    )
    for start in candidates:
        opening = source.find("{", start.start())
        if opening < 0 or source.find(";", start.start(), opening) >= 0:
            continue
        tokens = re.finditer(
            r"/\*.*?\*/|//[^\n]*|\"(?:\\.|[^\"\\])*\"|"
            r"'(?:\\.|[^'\\])*'|[{}]",
            source[opening:],
            re.S,
        )
        depth = 0
        for token in tokens:
            if token[0] == "{":
                depth += 1
            elif token[0] == "}":
                depth -= 1
                if depth == 0:
                    return source[start.start() : opening + token.end()]
        raise ValueError(f"unterminated production function {name}")
    raise ValueError(f"missing production function {name}")


def extract_type(source, name):
    match = re.search(
        r"typedef\s+struct\s*\{[^}]*\}\s*" + re.escape(name) + r"\s*;",
        source,
        re.S,
    )
    if not match:
        raise ValueError(f"missing production type {name}")
    return match[0]


PREFIX = r'''
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
typedef int32_t LONG;
typedef uint32_t DWORD;
typedef uint8_t BYTE;
typedef uint32_t ULONG_PTR;
typedef struct { LONG x,y; } POINT;
typedef struct { float l,t,r,b; } UIRectF;
#define WINAPI __attribute__((stdcall))
#define PRM_UI_CAPTURE_RVA 0x10UL
#define PRM_MOUSE_X_RVA 0x100UL
#define PRM_MOUSE_Y_RVA 0x104UL
#define PAGE_GUARD 0x100UL
#define PAGE_NOACCESS 0x01UL
#define MEM_COMMIT 0x1000UL
typedef DWORD (__attribute__((thiscall)) *PFN_OwnerWindowUpdate)(void*);
'''


STUBS = r'''
#define NATIVE_COUNT 6
#define VT_COUNT 8
#define FAKE_EXE_SIZE 0x200UL

typedef struct {
    void **vt;
    BYTE pad[0x30];
} NativeWindow;

static NativeWindow g_native[NATIVE_COUNT];
static void *g_vtables[VT_COUNT][32];
static BYTE g_fake_exe[FAKE_EXE_SIZE];
static BYTE *g_exe=g_fake_exe;
static DWORD g_exe_size=sizeof(g_fake_exe);
static LONG *g_mouse_x=(LONG *)(g_fake_exe+PRM_MOUSE_X_RVA);
static LONG *g_mouse_y=(LONG *)(g_fake_exe+PRM_MOUSE_Y_RVA);

static OwnerInputRegion g_owner_input_regions[16];
static DWORD g_owner_input_region_count;
static DWORD g_ui_present_serial;
static DWORD g_owner_capture_object;
static DWORD g_owner_mapped_mouse;
static int g_owner_input_remap_enabled;
static int g_owner_scale_enabled;
static int g_input_enabled;
static int g_input_runtime_enabled;
static int g_ui_runtime_enabled;
static int g_owner_bitmap_hooks_installed;
static int g_locked;
static float g_scale;
static DWORD g_thread_id;
static DWORD g_owner_hit_hooks_installed;
static DWORD g_owner_update_calls,g_owner_update_scoped,g_owner_update_rejected;
static OwnerHitSelection g_owner_hit_selection;
static DWORD g_owner_callback_count[NATIVE_COUNT];
static LONG g_owner_seen_x[NATIVE_COUNT],g_owner_seen_y[NATIVE_COUNT];
static int g_owner_seen_selected[NATIVE_COUNT];
static int g_mutate_callback;
static int g_nested_callback;
static DWORD g_nested_obj;
static DWORD g_nested_seen_x,g_nested_seen_y;

DWORD WINAPI owner_window_update_c(DWORD);

static int range_readable(const void *p,DWORD bytes,const void *base,size_t size) {
    uintptr_t q=(uintptr_t)p,b=(uintptr_t)base;
    if(!p || !bytes || q<b || q>b+size) return 0;
    return (uintptr_t)bytes <= b+size-q;
}
static int mem_readable(const void *p,DWORD bytes) {
    return range_readable(p,bytes,g_native,sizeof(g_native)) ||
           range_readable(p,bytes,g_vtables,sizeof(g_vtables)) ||
           range_readable(p,bytes,g_fake_exe,sizeof(g_fake_exe));
}
static void owner_input_region_lock(void) { assert(!g_locked); g_locked=1; }
static void owner_input_region_unlock(void) { assert(g_locked); g_locked=0; }
static float ui_scale_factor(void) { return g_scale; }
static DWORD current_thread(void) { return g_thread_id; }
static DWORD (*g_GetCurrentThreadId)(void)=current_thread;

static DWORD native_index(void *self) {
    DWORD i;
    for(i=0;i<NATIVE_COUNT;++i) if(self==&g_native[i]) return i;
    return UINT32_MAX;
}
static DWORD __attribute__((thiscall)) native_update(void *self) {
    DWORD i=native_index(self);
    if(i==UINT32_MAX) return 0;
    ++g_owner_callback_count[i];
    g_owner_seen_x[i]=*g_mouse_x;
    g_owner_seen_y[i]=*g_mouse_y;
    /* This is the native shortcut-slot boundary: an outside point clears the
       selected slot, while a point inside the native hotbar selects it. */
    g_owner_seen_selected[i]=(*g_mouse_x>=0 && *g_mouse_x<600 &&
                              *g_mouse_y>=0 && *g_mouse_y<=300);
    if((DWORD)(ULONG_PTR)self==g_nested_obj) {
        g_nested_seen_x=(DWORD)*g_mouse_x;
        g_nested_seen_y=(DWORD)*g_mouse_y;
    }
    if(g_nested_callback && i==0) {
        g_nested_callback=0;
        g_nested_seen_x=g_nested_seen_y=0;
        owner_window_update_c(g_nested_obj);
        g_nested_callback=1;
    }
    if(g_mutate_callback) {
        *g_mouse_x=0x1234; *g_mouse_y=-0x2345;
        g_owner_hit_selection.valid=0;
    }
    return 0x70000000UL+i;
}
'''


TESTS = r'''
static DWORD native_ptr(DWORD i) { return (DWORD)(ULONG_PTR)&g_native[i]; }

static void reset_all(void) {
    DWORD i,j;
    memset(g_native,0,sizeof(g_native));
    memset(g_vtables,0,sizeof(g_vtables));
    memset(g_fake_exe,0,sizeof(g_fake_exe));
    memset(g_owner_input_regions,0,sizeof(g_owner_input_regions));
    memset(&g_owner_hit_selection,0,sizeof(g_owner_hit_selection));
    memset(g_owner_callback_count,0,sizeof(g_owner_callback_count));
    memset(g_owner_seen_x,0,sizeof(g_owner_seen_x));
    memset(g_owner_seen_y,0,sizeof(g_owner_seen_y));
    memset(g_owner_seen_selected,0,sizeof(g_owner_seen_selected));
    for(i=0;i<NATIVE_COUNT;++i) g_native[i].vt=&g_vtables[i][0];
    for(i=0;i<VT_COUNT;++i)
        for(j=0;j<32;++j) g_vtables[i][j]=0;
    for(i=0;i<NATIVE_COUNT;++i) g_vtables[i][0x40/4]=(void*)native_update;
    g_exe=g_fake_exe; g_exe_size=sizeof(g_fake_exe);
    g_mouse_x=(LONG *)(g_fake_exe+PRM_MOUSE_X_RVA);
    g_mouse_y=(LONG *)(g_fake_exe+PRM_MOUSE_Y_RVA);
    g_owner_input_region_count=0; g_ui_present_serial=100;
    g_owner_capture_object=0; g_owner_mapped_mouse=0;
    g_owner_input_remap_enabled=g_owner_scale_enabled=1;
    g_input_enabled=g_input_runtime_enabled=g_ui_runtime_enabled=1;
    g_owner_bitmap_hooks_installed=1; g_owner_hit_hooks_installed=1;
    g_locked=0; g_scale=2.0f; g_thread_id=17;
    g_mutate_callback=0; g_nested_callback=0; g_nested_obj=0;
    g_nested_seen_x=g_nested_seen_y=0;
    *g_mouse_x=350; *g_mouse_y=25;
    *(DWORD *)(g_fake_exe+PRM_UI_CAPTURE_RVA)=0;
}

static void add_region(unsigned int n,DWORD object,DWORD present,
                       float l,float t,float r,float b,float ax,float ay,
                       DWORD input_order,DWORD exact_order,int native_size) {
    OwnerInputRegion *m=&g_owner_input_regions[n];
    memset(m,0,sizeof(*m));
    m->rect=(UIRectF){l,t,r,b}; m->ax=ax; m->ay=ay; m->fit_scale=g_scale;
    m->offset_x=m->offset_y=0; m->object_ptr=object; m->present=present;
    m->input_order=input_order; m->exact_order=exact_order;
    m->vtable_ptr=*(DWORD *)(ULONG_PTR)object; m->native_size=native_size;
    if(g_owner_input_region_count<=n) g_owner_input_region_count=n+1;
}

static void publish_hit(DWORD object,DWORD raw_x,DWORD raw_y,
                        DWORD mapped_x,DWORD mapped_y) {
    OwnerHitSelection *h=&g_owner_hit_selection;
    memset(h,0,sizeof(*h));
    h->raw.x=(LONG)raw_x; h->raw.y=(LONG)raw_y;
    h->mapped.x=(LONG)mapped_x; h->mapped.y=(LONG)mapped_y;
    h->thread=g_thread_id; h->valid=1;
    *g_mouse_x=(LONG)mapped_x; *g_mouse_y=(LONG)mapped_y;
    if(object) {
        unsigned int i;
        for(i=0;i<g_owner_input_region_count;++i)
            if(g_owner_input_regions[i].object_ptr==object) { h->region=g_owner_input_regions[i]; break; }
    }
}

static void expect_seen(DWORD i,LONG x,LONG y,int selected) {
    assert(g_owner_seen_x[i]==x && g_owner_seen_y[i]==y);
    assert(g_owner_seen_selected[i]==selected);
}

static void test_scaled_hover_and_old_rect_miss(void) {
    DWORD result;
    reset_all();
    add_region(0,native_ptr(0),g_ui_present_serial,230,0,520,67,0,0,10,10,0);

    /* Visual 200% hotbar point (700,50) is already mapped by ScreenToClient
       to native (350,25). The callback must not divide it a second time. */
    publish_hit(native_ptr(0),700,50,350,25);
    result=owner_window_update_c(native_ptr(0));
    assert(result==0x70000000UL);
    expect_seen(0,350,25,1);
    assert(*g_mouse_x==350 && *g_mouse_y==25);

    /* Native old location (350,25) is outside the displayed 460..1040 box.
       A valid visual miss has no owner identity, so the known root gets the
       temporary outside point and its native slot clears. */
    publish_hit(0,350,25,350,25);
    result=owner_window_update_c(native_ptr(0));
    assert(result==0x70000000UL);
    expect_seen(0,-32768,-32768,0);
    assert(*g_mouse_x==350 && *g_mouse_y==25);
    puts("PASS: scaled hotbar hover uses one inverse map; old unscaled location clears the known root");
}

static void test_overlap_and_arbitrary_roots(void) {
    reset_all();
    add_region(0,native_ptr(0),g_ui_present_serial,200,100,500,300,0,0,10,10,0);
    add_region(1,native_ptr(1),g_ui_present_serial,200,100,500,300,0,0,20,20,0);
    publish_hit(native_ptr(1),600,300,300,150);
    assert(owner_window_update_c(native_ptr(0))==0x70000000UL);
    expect_seen(0,-32768,-32768,0);
    assert(owner_window_update_c(native_ptr(1))==0x70000001UL);
    expect_seen(1,300,150,1);

    /* No RTTI/class spelling participates in admission or dispatch. */
    reset_all();
    g_scale=1.33f;
    add_region(3,native_ptr(3),g_ui_present_serial,400,200,560,320,0,0,7,7,0);
    publish_hit(native_ptr(3),532,266,400,200);
    assert(owner_window_update_c(native_ptr(3))==0x70000003UL);
    expect_seen(3,400,200,1);
    assert(*g_mouse_x==400 && *g_mouse_y==200);
    puts("PASS: visual topmost selection filters competing roots and anonymous roots use the same property path");
}

static void test_identity_and_gate_fallbacks(void) {
    reset_all();
    add_region(0,native_ptr(0),g_ui_present_serial,230,0,520,67,0,0,1,1,0);
    publish_hit(native_ptr(0),700,50,350,25);

    /* A changed copied snapshot must not cause a second map or a stale guard. */
    g_owner_input_regions[0].offset_x=9;
    assert(owner_window_update_c(native_ptr(0))==0x70000000UL);
    expect_seen(0,350,25,1);

    reset_all();
    add_region(0,native_ptr(0),g_ui_present_serial-3,230,0,520,67,0,0,1,1,0);
    publish_hit(native_ptr(0),700,50,350,25);
    assert(owner_window_update_c(native_ptr(0))==0x70000000UL);
    expect_seen(0,350,25,1);

    reset_all();
    add_region(0,native_ptr(0),g_ui_present_serial,230,0,520,67,0,0,1,1,0);
    publish_hit(native_ptr(0),700,50,350,25);
    g_native[0].vt=&g_vtables[VT_COUNT-1][0];
    g_vtables[VT_COUNT-1][0x40/4]=(void*)native_update;
    assert(owner_window_update_c(native_ptr(0))==0x70000000UL);
    expect_seen(0,350,25,1);

    reset_all();
    add_region(0,native_ptr(0),g_ui_present_serial,230,0,520,67,0,0,1,1,0);
    publish_hit(native_ptr(0),700,50,350,25);
    g_owner_input_remap_enabled=0;
    assert(owner_window_update_c(native_ptr(0))==0x70000000UL);
    expect_seen(0,350,25,1);

    reset_all();
    add_region(0,native_ptr(0),g_ui_present_serial,230,0,520,67,0,0,1,1,0);
    publish_hit(native_ptr(0),700,50,350,25);
    *(DWORD *)(g_fake_exe+PRM_UI_CAPTURE_RVA)=native_ptr(2);
    assert(owner_window_update_c(native_ptr(0))==0x70000000UL);
    expect_seen(0,350,25,1);

    reset_all();
    add_region(0,native_ptr(0),g_ui_present_serial,230,0,520,67,0,0,1,1,1);
    publish_hit(native_ptr(0),350,25,350,25);
    assert(owner_window_update_c(native_ptr(0))==0x70000000UL);
    expect_seen(0,350,25,1);

    reset_all();
    /* Unknown roots retain native behavior even with a valid owner sample. */
    add_region(0,native_ptr(0),g_ui_present_serial,230,0,520,67,0,0,1,1,0);
    publish_hit(native_ptr(0),700,50,350,25);
    assert(owner_window_update_c(native_ptr(1))==0x70000001UL);
    expect_seen(1,350,25,1);
    puts("PASS: stale/vtable-reused, disabled, capture, native-size, and unknown roots fall through unchanged");
}

static void test_mapping_revalidation_and_restore(void) {
    reset_all();
    add_region(0,native_ptr(0),g_ui_present_serial,230,0,520,67,0,0,1,1,0);
    publish_hit(native_ptr(0),700,50,349,25);
    /* Fresh region maps raw (700,50) to (350,25), so a mismatched saved pair
       cannot be silently mapped again; callback receives the original pair. */
    assert(owner_window_update_c(native_ptr(0))==0x70000000UL);
    expect_seen(0,349,25,1);
    assert(*g_mouse_x==349 && *g_mouse_y==25);

    reset_all();
    add_region(0,native_ptr(0),g_ui_present_serial,230,0,520,67,0,0,1,1,0);
    publish_hit(native_ptr(0),700,50,350,25);
    g_mutate_callback=1;
    assert(owner_window_update_c(native_ptr(0))==0x70000000UL);
    expect_seen(0,350,25,1);
    assert(*g_mouse_x==350 && *g_mouse_y==25);
    assert(!g_owner_hit_selection.valid); /* callback mutation cannot alter wrapper's restoration */

    reset_all();
    add_region(0,native_ptr(0),g_ui_present_serial,230,0,520,67,0,0,1,1,0);
    add_region(1,native_ptr(1),g_ui_present_serial,0,0,700,300,0,0,0,0,0);
    publish_hit(native_ptr(0),700,50,350,25);
    g_nested_callback=1; g_nested_obj=native_ptr(1);
    assert(owner_window_update_c(native_ptr(0))==0x70000000UL);
    expect_seen(0,350,25,1);
    assert(g_nested_seen_x==(DWORD)-32768 && g_nested_seen_y==(DWORD)-32768);
    assert(*g_mouse_x==350 && *g_mouse_y==25);
    puts("PASS: fresh mapping mismatch forwards untouched; callback mutation and nested dispatch restore the native/world pair");
}

int main(void) {
    test_scaled_hover_and_old_rect_miss();
    test_overlap_and_arbitrary_roots();
    test_identity_and_gate_fallbacks();
    test_mapping_revalidation_and_restore();
    return 0;
}
'''


def main():
    source = (ROOT / "prm_uifix.c").read_text()
    types = "\n".join(
        extract_type(source, name)
        for name in ("OwnerInputRegion", "OwnerHitSelection")
    )
    functions = "\n".join(
        extract_function(source, name)
        for name in (
            "rect_contains_point",
            "rect_area",
            "owner_native_capture",
            "owner_input_region_bounds",
            "owner_input_map_region",
            "owner_input_select_region",
            "owner_window_update_c",
        )
    )
    code = PREFIX + types + STUBS + functions + TESTS
    with tempfile.TemporaryDirectory(prefix="prm-hover-test-") as directory:
        harness = Path(directory) / "hover.c"
        binary = Path(directory) / "hover-test"
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
    print("PASS: extracted owner-window update bridge with 32-bit ASan/UBSan native callbacks")


if __name__ == "__main__":
    main()
