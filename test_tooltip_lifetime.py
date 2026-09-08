#!/usr/bin/env python3
"""Exercise generic tooltip source provenance across native refreshes.

The harness extracts the production refresh callback and popup offset helper
into a 32-bit fixture.  It models the native controller's +1C popup and +20
clock fields, while all source transforms are copied input-region snapshots.
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
    match = re.search(r"typedef\s+struct\s*\{[^}]*\}\s*" +
                      re.escape(name) + r"\s*;", SOURCE)
    if not match:
        raise RuntimeError(f"missing production type {name}")
    return match[0]


def extract_function(name):
    start = re.search(r"^(?:static\s+)?[A-Za-z_][A-Za-z0-9_\s\*]*\b" + re.escape(name) +
                      r"\s*\([^;]*?\)\s*\{", SOURCE, re.M)
    if not start:
        raise RuntimeError(f"missing production function {name}")
    opening = SOURCE.find("{", start.start())
    depth = 0
    tokens = re.finditer(
        r'/\*.*?\*/|//[^\n]*|"(?:\\.|[^"\\])*"|'
        r"'(?:\\.|[^'\\])*'|[{}]", SOURCE[opening:], re.S)
    for token in tokens:
        if token[0] == "{":
            depth += 1
        elif token[0] == "}":
            depth -= 1
            if depth == 0:
                return SOURCE[start.start():opening + token.end()]
    raise RuntimeError(f"unterminated production function {name}")


PREFIX = r'''
#include <assert.h>
#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
typedef uint32_t DWORD;
typedef int32_t LONG;
typedef uint8_t BYTE;
typedef uintptr_t ULONG_PTR;
typedef DWORD (*PFN_GetTickCount)(void);
typedef struct { LONG x,y; } POINT;
typedef struct { float l,t,r,b; } UIRectF;
#define WINAPI __attribute__((stdcall))
#define PRM_TOOLTIP_MANAGER_RVA 0x00A78D8CUL
#define PRM_UI_CAPTURE_RVA 0x00AB786CUL
#define CHECK(x) do { if (!(x)) { \
    fprintf(stderr,"check failed at line %d: %s\n",__LINE__,#x); exit(1); \
} } while (0)
'''


STUBS = r'''
enum { ROOT_A=0, ROOT_B=1, ROOT_UNKNOWN=2, ROOT_COUNT=3 };
typedef struct { BYTE bytes[0x50]; } FakeObject;
static FakeObject g_objects[ROOT_COUNT];
static BYTE g_popup_a[0x20],g_popup_b[0x20],g_speech[0x20];
static BYTE* g_exe;
static DWORD g_exe_size;
static DWORD g_ui_present_serial;
static DWORD g_owner_input_region_count;
static OwnerInputRegion g_owner_input_regions[8];
static OwnerHitSelection g_owner_hit_selection;
static OwnerTooltipBinding g_owner_tooltip_binding;
static PFN_GetTickCount g_owner_tooltip_clock;
static DWORD g_clock_value,g_clock_calls,g_thread_id;
static int g_locked;
static int g_owner_input_remap_enabled,g_owner_scale_enabled;
static int g_input_enabled,g_input_runtime_enabled,g_ui_runtime_enabled;
static float g_scale;
static DWORD g_capture;

static int range_readable(const void* p,DWORD bytes,const void* base,size_t size) {
    uintptr_t q=(uintptr_t)p,b=(uintptr_t)base;
    if(!p || !bytes || q<b || q>b+size) return 0;
    return (uintptr_t)bytes<=b+size-q;
}
static int mem_readable(const void* p,DWORD bytes) {
    return range_readable(p,bytes,g_objects,sizeof(g_objects)) ||
           range_readable(p,bytes,g_popup_a,sizeof(g_popup_a)) ||
           range_readable(p,bytes,g_popup_b,sizeof(g_popup_b)) ||
           range_readable(p,bytes,g_speech,sizeof(g_speech)) ||
           range_readable(p,bytes,g_exe,g_exe_size);
}
static int s_equal(const char* a,const char* b) { return a && b && !strcmp(a,b); }
static float ui_scale_factor(void) { return g_scale; }
static DWORD current_thread(void) { return g_thread_id; }
static DWORD (*g_GetCurrentThreadId)(void)=current_thread;
static void owner_input_region_lock(void) { CHECK(!g_locked); g_locked=1; }
static void owner_input_region_unlock(void) { CHECK(g_locked); g_locked=0; }
static DWORD fake_clock(void) { ++g_clock_calls; return g_clock_value; }
static DWORD owner_native_capture(void) { return g_capture; }
'''


TESTS = r'''
static DWORD object_ptr(int index) { return (DWORD)(ULONG_PTR)&g_objects[index]; }
static DWORD popup_ptr(BYTE* popup) { return (DWORD)(ULONG_PTR)popup; }
static void setup(void) {
    DWORD i;
    if(!g_exe) {
        g_exe_size=PRM_TOOLTIP_MANAGER_RVA+0x100UL;
        g_exe=(BYTE*)calloc(1,g_exe_size);
        CHECK(g_exe!=0);
    }
    memset(g_objects,0,sizeof(g_objects));
    memset(g_popup_a,0,sizeof(g_popup_a));
    memset(g_popup_b,0,sizeof(g_popup_b));
    memset(g_speech,0,sizeof(g_speech));
    memset(&g_owner_hit_selection,0,sizeof(g_owner_hit_selection));
    memset(&g_owner_tooltip_binding,0,sizeof(g_owner_tooltip_binding));
    memset(g_owner_input_regions,0,sizeof(g_owner_input_regions));
    memset(g_exe,0,g_exe_size);
    g_owner_input_region_count=0;
    g_ui_present_serial=100;
    g_clock_value=400; g_clock_calls=0; g_thread_id=77;
    g_locked=0; g_capture=0; g_scale=2.0f;
    g_owner_input_remap_enabled=1; g_owner_scale_enabled=1;
    g_input_enabled=1; g_input_runtime_enabled=1; g_ui_runtime_enabled=1;
    g_owner_tooltip_clock=fake_clock;
    for(i=0;i<ROOT_COUNT;++i) *(DWORD*)g_objects[i].bytes=0x10000000UL+i*0x1000UL;
    *(DWORD*)(g_exe+PRM_TOOLTIP_MANAGER_RVA)=object_ptr(ROOT_UNKNOWN);
    /* The controller is the ROOT_UNKNOWN object in this fixture. */
    *(DWORD*)(g_objects[ROOT_UNKNOWN].bytes+0x1c)=popup_ptr(g_popup_a);
    *(DWORD*)(g_objects[ROOT_UNKNOWN].bytes+0x20)=g_clock_value;
}
static void add_region(int root,float ax,float ay,float scale,float dx,float dy) {
    OwnerInputRegion* r=&g_owner_input_regions[0];
    memset(r,0,sizeof(*r));
    r->rect=(UIRectF){100,200,500,500};
    r->ax=ax; r->ay=ay; r->fit_scale=scale; r->offset_x=dx; r->offset_y=dy;
    r->object_ptr=object_ptr(root); r->present=g_ui_present_serial;
    r->input_order=10; r->exact_order=10; r->vtable_ptr=0x50000000UL+root*0x1000UL;
    g_owner_input_region_count=1;
    g_owner_hit_selection.region=*r;
    /* The right-anchored B rectangle extends to x=250 at 150%; use a raw
       point inside it so the refresh callback can validate that root. */
    g_owner_hit_selection.raw=(POINT){root==ROOT_B?100:300,root==ROOT_B?400:-100};
    g_owner_hit_selection.mapped=(POINT){600,800};
    g_owner_hit_selection.thread=g_thread_id;
    g_owner_hit_selection.valid=1;
}
static void controller_write_tick(DWORD tick) {
    *(DWORD*)(g_objects[ROOT_UNKNOWN].bytes+0x20)=tick;
}
static DWORD native_refresh(void) {
    DWORD tick=owner_tooltip_refresh_c(object_ptr(ROOT_UNKNOWN));
    controller_write_tick(tick);
    return tick;
}
static void popup_state(OwnerWindowState* st,DWORD popup,const char* name) {
    memset(st,0,sizeof(*st)); st->object_ptr=popup; strcpy(st->class_name,name);
}
static void offset_for(OwnerWindowState* st,float* dx,float* dy) {
    owner_popup_offset(st,250,450,dx,dy);
}
static void expect_offset(OwnerWindowState* st,float want_x,float want_y) {
    float dx=31.0f,dy=-17.0f;
    offset_for(st,&dx,&dy);
    CHECK(fabsf(dx-want_x)<0.001f && fabsf(dy-want_y)<0.001f);
}
static void expect_unchanged(OwnerWindowState* st) {
    float dx=31.0f,dy=-17.0f;
    offset_for(st,&dx,&dy);
    CHECK(dx==31.0f && dy==-17.0f);
}
static void test_refresh_and_leave_reentry(void) {
    OwnerWindowState popup;
    setup(); add_region(ROOT_A,0,1000,2.0f,7.0f,-3.0f);
    CHECK(native_refresh()==400 && g_clock_calls==1);
    popup_state(&popup,popup_ptr(g_popup_a),"UITransBalloonText");
    /* x=250,y=450 under source (ax=0,ay=1000), scale 2, offsets 7,-3. */
    expect_offset(&popup,257.0f,-553.0f);

    /* Native leave clears the copied hit and region; native popup remains
       registered until its own expiry, so the last refresh source remains. */
    memset(&g_owner_hit_selection,0,sizeof(g_owner_hit_selection));
    g_owner_input_region_count=0;
    expect_offset(&popup,257.0f,-553.0f);

    /* Reentering another root before its factory refresh must not teleport the
       old popup to that root.  Once the factory refreshes, the source changes. */
    add_region(ROOT_B,1000,0,1.5f,11.0f,13.0f);
    expect_offset(&popup,257.0f,-553.0f);
    CHECK(native_refresh()==400 && g_clock_calls==2); /* same clock tick */
    expect_offset(&popup,-364.0f,238.0f);
    puts("PASS refresh/leave/reentry: source remains through leave and updates on same-tick factory refresh");
}
static void test_unrelated_and_new_popup(void) {
    OwnerWindowState popup;
    setup(); add_region(ROOT_A,0,1000,2.0f,0,0); CHECK(native_refresh()==400);
    popup_state(&popup,popup_ptr(g_popup_a),"UITransBalloonText");
    expect_offset(&popup,250.0f,-550.0f);

    /* A factory call with a valid-looking hit that is absent from the fresh
       copied region fails closed and cannot retain root A's source. */
    memset(&g_owner_hit_selection,0,sizeof(g_owner_hit_selection));
    g_owner_input_region_count=0;
    CHECK(native_refresh()==400);
    expect_unchanged(&popup);

    /* The clock runs before native allocates/reuses the popup. Binding by
       controller lets the newly created popup use the just-refreshed source. */
    add_region(ROOT_B,1000,0,1.5f,11.0f,13.0f);
    g_clock_value=401; CHECK(native_refresh()==401);
    *(DWORD*)(g_objects[ROOT_UNKNOWN].bytes+0x1c)=popup_ptr(g_popup_b);
    popup_state(&popup,popup_ptr(g_popup_b),"UITransBalloonText");
    expect_offset(&popup,-364.0f,238.0f);
    puts("PASS unrelated/new popup: invalid refresh clears provenance and controller binding covers post-clock popup creation");
}
static void test_guards_and_world_speech(void) {
    OwnerWindowState popup,speech;
    setup(); add_region(ROOT_A,0,1000,2.0f,0,0); CHECK(native_refresh()==400);
    popup_state(&popup,popup_ptr(g_popup_a),"UITransBalloonText");
    expect_offset(&popup,250.0f,-550.0f);

    /* A changed native +20 means the binding no longer describes the current
       factory refresh.  The copied output remains untouched. */
    controller_write_tick(401); expect_unchanged(&popup); controller_write_tick(400);
    popup_state(&speech,popup_ptr(g_speech),"UITransBalloonText");
    expect_unchanged(&speech); /* same class, different native owner */

    /* Capture/disabled refreshes clear the source instead of borrowing a
       previous root. */
    g_capture=object_ptr(ROOT_A); CHECK(native_refresh()==400); expect_unchanged(&popup);
    g_capture=0; add_region(ROOT_A,0,1000,2.0f,0,0); CHECK(native_refresh()==400);
    g_ui_runtime_enabled=0; expect_unchanged(&popup);
    puts("PASS guards: +20 mismatch, world-speech identity, capture, and disabled refreshes fail closed");
}
int main(void) {
    CHECK(sizeof(void*)==4);
    test_refresh_and_leave_reentry();
    test_unrelated_and_new_popup();
    test_guards_and_world_speech();
    puts("PASS generic tooltip lifetime harness: 32-bit ASan/UBSan");
    return 0;
}
'''


def main():
    types = "\n".join(extract_type(name) for name in (
        "OwnerWindowState", "OwnerInputRegion", "OwnerHitSelection", "OwnerTooltipBinding"))
    functions = "\n".join(extract_function(name) for name in (
        "rect_contains_point", "rect_area",
        "owner_input_region_bounds", "owner_input_select_region",
        "owner_tooltip_controller_is_current", "owner_tooltip_publish_refresh",
        "owner_tooltip_refresh_c", "owner_is_transient_tooltip", "owner_popup_offset"))
    code = PREFIX + types + STUBS + functions + TESTS
    with tempfile.TemporaryDirectory(prefix="prm-tooltip-lifetime-") as directory:
        harness = Path(directory) / "tooltip.c"
        binary = Path(directory) / "tooltip-test"
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
    print("PASS: extracted generic tooltip lifetime functions with 32-bit ASan/UBSan fixture")


if __name__ == "__main__":
    main()
