#!/usr/bin/env python3
"""Exercise bounded owner-state reclamation with a 32-bit native-shaped fixture.

The fixture extracts the production owner admission/reclamation functions.  It
fills all 512 state slots, models UIWindowMgr's intrusive lists, and uses real
object/vtable identities so stale tooltip churn cannot silently remove an
active or recently published owner.
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
    match = re.search(
        r"^static [^\n]*\b" + re.escape(name) + r"\s*\([^;]*?\)\s*\{",
        SOURCE,
        re.M,
    )
    if not match:
        raise RuntimeError(f"missing production function {name}")
    opening = SOURCE.find("{", match.start())
    depth = 0
    for token in re.finditer(r"/\*.*?\*/|//[^\n]*|\"(?:\\.|[^\"\\])*\"|'(?:\\.|[^'\\])*'|[{}]", SOURCE[opening:], re.S):
        if token[0] == "{":
            depth += 1
        elif token[0] == "}":
            depth -= 1
            if depth == 0:
                return SOURCE[match.start() : opening + token.end()]
    raise RuntimeError(f"unterminated production function {name}")


PREFIX = r'''
#include <assert.h>
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
#define MAX_OWNER_WINDOWS 512
#define CHECK(x) do { if (!(x)) { \
    fprintf(stderr,"check failed at line %d: %s\n",__LINE__,#x); exit(1); \
} } while (0)
'''


STUBS = r'''
static DWORD g_ui_present_serial;
static DWORD g_owner_input_max_age_presents=24;
static DWORD g_current_ui_owner;
static DWORD g_exe_size;
static BYTE* g_exe;

static OwnerWindowState g_owner_windows[MAX_OWNER_WINDOWS];
static DWORD g_owner_window_count;
static DWORD g_owner_window_reclaimed;
static DWORD g_owner_window_reclaim_blocked;
static OwnerHitSelection g_owner_hit_selection;
static OwnerBitmapScope g_owner_bitmap_scope;
static DWORD g_owner_capture_object,g_owner_capture_root;
static OwnerWindowState* owner_state_for(DWORD object,int create);
static int g_region_locked;
static void owner_input_region_lock(void) { CHECK(!g_region_locked); g_region_locked=1; }
static void owner_input_region_unlock(void) { CHECK(g_region_locked); g_region_locked=0; }

typedef struct { void* vt; char name[72]; } FakeObject;
typedef struct { DWORD next,prev,obj; } FakeNode;
#define FAKE_OBJECTS 1024
static FakeObject g_objects[FAKE_OBJECTS];
static void* g_vtables[FAKE_OBJECTS][4];
static FakeNode g_nodes[16];

static int range_readable(const void* p,DWORD bytes,const void* base,size_t size) {
    uintptr_t q=(uintptr_t)p,b=(uintptr_t)base;
    if(!p || q<b || q>b+size) return 0;
    return (uintptr_t)bytes<=b+size-q;
}
static int mem_readable(const void* p,DWORD bytes) {
    return range_readable(p,bytes,g_objects,sizeof(g_objects)) ||
           range_readable(p,bytes,g_vtables,sizeof(g_vtables)) ||
           range_readable(p,bytes,g_nodes,sizeof(g_nodes)) ||
           range_readable(p,bytes,g_exe,g_exe_size);
}
static unsigned int s_len(const char* s) {
    unsigned int n=0; if(!s) return 0; while(s[n]) ++n; return n;
}
static void s_copy(char* dst,unsigned int cap,const char* src) {
    unsigned int i=0; if(!dst || !cap) return;
    if(!src) { dst[0]=0; return; }
    while(src[i] && i+1<cap) { dst[i]=src[i]; ++i; }
    dst[i]=0;
}
static int rtti_name_from_object(DWORD objv,char* out,unsigned int cap,DWORD* out_vtable_rva) {
    DWORD i;
    if(out_vtable_rva) *out_vtable_rva=0;
    if(!out || cap<2) return 0;
    for(i=0;i<FAKE_OBJECTS;++i) if(objv==(DWORD)(ULONG_PTR)&g_objects[i]) {
        strncpy(out,g_objects[i].name,cap-1); out[cap-1]=0;
        if(out_vtable_rva) *out_vtable_rva=(DWORD)(ULONG_PTR)g_objects[i].vt;
        return out[0]!=0;
    }
    out[0]=0; return 0;
}

static void fake_object(DWORD index,const char* class_name) {
    memset(&g_objects[index],0,sizeof(g_objects[index]));
    g_objects[index].vt=&g_vtables[index][0];
    strncpy(g_objects[index].name,class_name,sizeof(g_objects[index].name)-1);
}
static DWORD fake_ptr(DWORD index) { return (DWORD)(ULONG_PTR)&g_objects[index]; }
static DWORD fake_vt(DWORD index) { return (DWORD)(ULONG_PTR)g_objects[index].vt; }

static void clear_manager(void) {
    DWORD i;
    memset(g_nodes,0,sizeof(g_nodes));
    if(g_exe) for(i=0;i<4;++i) {
        g_nodes[i].next=(DWORD)(ULONG_PTR)&g_nodes[i];
        g_nodes[i].prev=(DWORD)(ULONG_PTR)&g_nodes[i];
        *(DWORD*)(g_exe+0xab76d8UL+(0x174UL+i*8UL))=(DWORD)(ULONG_PTR)&g_nodes[i];
    }
}
static void manager_activate(DWORD object) {
    FakeNode* head; FakeNode* node=&g_nodes[4];
    clear_manager();
    head=&g_nodes[0];
    head->next=(DWORD)(ULONG_PTR)node;
    head->prev=(DWORD)(ULONG_PTR)node;
    node->next=(DWORD)(ULONG_PTR)head;
    node->prev=(DWORD)(ULONG_PTR)head;
    node->obj=object;
}
static void reset_fixture(void) {
    DWORD i;
    if(!g_exe) {
        g_exe_size=0xab76d8UL+0x200UL;
        g_exe=(BYTE*)calloc(1,g_exe_size);
        CHECK(g_exe!=0);
    }
    memset(g_owner_windows,0,sizeof(g_owner_windows));
    memset(g_objects,0,sizeof(g_objects));
    memset(g_vtables,0,sizeof(g_vtables));
    memset(&g_owner_hit_selection,0,sizeof(g_owner_hit_selection));
    memset(&g_owner_bitmap_scope,0,sizeof(g_owner_bitmap_scope));
    g_owner_window_count=0; g_owner_window_reclaimed=0; g_owner_window_reclaim_blocked=0;
    g_owner_capture_object=g_owner_capture_root=0; g_current_ui_owner=0;
    g_region_locked=0;
    g_ui_present_serial=1000; g_owner_input_max_age_presents=24;
    clear_manager();
    for(i=0;i<FAKE_OBJECTS;++i) fake_object(i,"UIItemWnd");
}
static OwnerWindowState* admit(DWORD index,const char* class_name) {
    strcpy(g_objects[index].name,class_name);
    return owner_state_for(fake_ptr(index),1);
}
static void fill_table(void) {
    DWORD i;
    for(i=0;i<MAX_OWNER_WINDOWS;++i) CHECK(admit(i,"UIItemWnd")!=0);
    CHECK(g_owner_window_count==MAX_OWNER_WINDOWS);
}
static void age_all(DWORD age) {
    DWORD i;
    for(i=0;i<MAX_OWNER_WINDOWS;++i) {
        g_owner_windows[i].last_present=g_ui_present_serial-age;
        g_owner_windows[i].frame_tag=0;
        g_owner_windows[i].last_draw_present=0;
        g_owner_windows[i].bitmap_present=0;
        g_owner_windows[i].last_input_present=0;
    }
}
'''


TESTS = r'''
static void test_oldest_stale_reclaimed(void) {
    OwnerWindowState* first; OwnerWindowState* second; OwnerWindowState* fresh;
    DWORD first_object,second_object;
    reset_fixture(); fill_table(); age_all(10);
    g_owner_windows[0].last_present=1;
    g_owner_windows[1].last_present=g_ui_present_serial-500;
    first=&g_owner_windows[0]; second=&g_owner_windows[1];
    first_object=first->object_ptr; second_object=second->object_ptr;
    fresh=admit(512,"UITransBalloonText");
    CHECK(fresh==first);
    CHECK(g_owner_window_count==MAX_OWNER_WINDOWS && g_owner_window_reclaimed==1);
    CHECK(fresh->object_ptr==fake_ptr(512));
    CHECK(owner_state_for(second_object,0)==second);
    CHECK(owner_state_for(first_object,0)==0);
    puts("PASS oldest stale owner state reclaimed while another stale root remains");
}

static void test_live_and_cached_states_protected(void) {
    DWORD active, recent, hit, scoped, current, captured, frame_recent, draw_recent;
    DWORD old_reclaimed; OwnerWindowState* fresh;
    reset_fixture(); fill_table(); age_all(1000);
    active=fake_ptr(0); recent=fake_ptr(1); hit=fake_ptr(2); scoped=fake_ptr(3);
    current=fake_ptr(4); captured=fake_ptr(5); frame_recent=fake_ptr(6); draw_recent=fake_ptr(7);
    manager_activate(active);
    g_owner_windows[1].last_present=g_ui_present_serial;
    g_owner_windows[2].last_input_present=g_ui_present_serial-10;
    g_owner_hit_selection.valid=1;
    g_owner_hit_selection.region.object_ptr=hit;
    g_owner_hit_selection.region.present=g_ui_present_serial;
    g_owner_bitmap_scope.object_ptr=scoped;
    g_current_ui_owner=current;
    g_owner_capture_object=captured;
    g_owner_windows[6].frame_tag=g_ui_present_serial+1;
    g_owner_windows[7].last_draw_present=g_ui_present_serial;
    old_reclaimed=g_owner_window_reclaimed;
    fresh=admit(512,"UITransBalloonText");
    CHECK(fresh!=0 && g_owner_window_reclaimed==old_reclaimed+1);
    CHECK(owner_state_for(active,0)!=0 && owner_state_for(recent,0)!=0);
    CHECK(owner_state_for(hit,0)!=0 && owner_state_for(scoped,0)!=0);
    CHECK(owner_state_for(current,0)!=0 && owner_state_for(captured,0)!=0);
    CHECK(owner_state_for(frame_recent,0)!=0 && owner_state_for(draw_recent,0)!=0);
    puts("PASS manager-active, current-scope, recent-draw, input-grace, and cached-hit owners survive reclamation");
}

static void test_mixed_activity_uses_most_recent_stamp(void) {
    DWORD mixed, older; OwnerWindowState* fresh;
    reset_fixture(); fill_table(); age_all(10);
    mixed=fake_ptr(0); older=fake_ptr(1);
    /* The first state has one very old stamp and one stale-but-newer stamp.
       The second state has only a middle-aged stamp.  Reclaiming by the
       oldest activity (minimum nonzero age) must choose the second state. */
    g_owner_windows[0].last_present=g_ui_present_serial-900;
    g_owner_windows[0].last_input_present=g_ui_present_serial-30;
    g_owner_windows[1].last_present=g_ui_present_serial-500;
    fresh=admit(512,"UITransBalloonText");
    CHECK(fresh==&g_owner_windows[1]);
    CHECK(owner_state_for(mixed,0)!=0 && owner_state_for(older,0)==0);
    puts("PASS mixed activity ages select the oldest state by most recent activity");
}

static void test_unreadable_manager_node_blocks_reclamation(void) {
    reset_fixture(); fill_table(); age_all(1000);
    g_nodes[0].next=0x12345678UL;
    CHECK(admit(512,"UITransBalloonText")==0);
    CHECK(g_owner_window_reclaimed==0 && g_owner_window_reclaim_blocked==1);
    puts("PASS unreadable or truncated manager list fails closed without eviction");
}

static void test_full_table_blocks_until_input_grace_expires(void) {
    OwnerWindowState* fresh;
    DWORD i;
    reset_fixture(); fill_table();
    for(i=0;i<MAX_OWNER_WINDOWS;++i) {
        g_owner_windows[i].last_present=g_ui_present_serial;
        g_owner_windows[i].last_input_present=g_ui_present_serial;
    }
    CHECK(admit(512,"UITransBalloonText")==0);
    CHECK(g_owner_window_reclaimed==0 && g_owner_window_reclaim_blocked==1);
    g_ui_present_serial+=3;
    CHECK(admit(513,"UITransBalloonText")==0);
    CHECK(g_owner_window_reclaim_blocked==2);
    g_ui_present_serial+=g_owner_input_max_age_presents+1;
    fresh=admit(514,"UITransBalloonText");
    CHECK(fresh!=0 && g_owner_window_reclaimed==1);
    puts("PASS full table blocks protected states and admits after input grace expires");
}

static void test_repeated_tooltip_reentry_preserves_active_root(void) {
    DWORD i; DWORD root; OwnerWindowState* fresh;
    reset_fixture(); fill_table(); age_all(1000);
    root=fake_ptr(0); manager_activate(root);
    for(i=512;i<640;++i) {
        fresh=admit(i,"UITransBalloonText");
        CHECK(fresh!=0);
        /* A just-entered tooltip is recent for this frame, then becomes stale
           after it leaves; the next re-entry must reclaim another old slot. */
        fresh->last_present=g_ui_present_serial;
        g_ui_present_serial+=30;
        CHECK(owner_state_for(root,0)!=0);
    }
    CHECK(g_owner_window_reclaimed>=128);
    CHECK(owner_state_for(root,0)!=0);
    puts("PASS repeated tooltip create/leave/re-entry churn without losing active root");
}

static void test_same_object_vtable_reuse_keeps_slot(void) {
    OwnerWindowState* old; OwnerWindowState* reused; DWORD object;
    reset_fixture(); old=admit(0,"UIItemWnd"); CHECK(old!=0); object=fake_ptr(0);
    g_objects[0].vt=&g_vtables[900][0]; strcpy(g_objects[0].name,"UITransBalloonText");
    reused=owner_state_for(object,1);
    CHECK(reused==old && g_owner_window_count==1);
    CHECK(reused->vtable_ptr==fake_vt(0) && reused->object_ptr==object);
    CHECK(g_owner_window_reclaimed==0 && g_owner_window_reclaim_blocked==0);
    puts("PASS reused native object with changed vtable reinitializes its existing slot");
}

int main(void) {
    test_oldest_stale_reclaimed();
    test_live_and_cached_states_protected();
    test_mixed_activity_uses_most_recent_stamp();
    test_unreadable_manager_node_blocks_reclamation();
    test_full_table_blocks_until_input_grace_expires();
    test_repeated_tooltip_reentry_preserves_active_root();
    test_same_object_vtable_reuse_keeps_slot();
    return 0;
}
'''


def main():
    types = "\n".join(
        extract_type(name)
        for name in ("OwnerWindowState", "OwnerInputRegion", "OwnerHitSelection", "OwnerBitmapScope")
    )
    functions = "\n".join(
        extract_function(name)
        for name in (
            "s_equal",
            "s_contains",
            "owner_class_is_hover_popup",
            "owner_class_is_world_label",
            "owner_class_is_world_title",
            "owner_class_is_world_name",
            "owner_class_should_hook",
            "rtti_image_readable",
            "rtti_type_is",
            "owner_rtti_window_family",
            "owner_object_should_hook",
            "owner_state_present_age",
            "owner_state_collect_manager",
            "owner_state_manager_active",
            "owner_state_reclaim_protected",
            "owner_state_activity_age",
            "owner_state_reclaim_slot",
            "owner_state_for",
        )
    )
    code = PREFIX + types + STUBS + functions + TESTS
    with tempfile.TemporaryDirectory(prefix="prm-owner-lifetime-") as directory:
        harness = Path(directory) / "owner_lifetime.c"
        binary = Path(directory) / "owner-lifetime"
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
    print("PASS: owner-state reclamation 32-bit ASan/UBSan fixture")


if __name__ == "__main__":
    main()
