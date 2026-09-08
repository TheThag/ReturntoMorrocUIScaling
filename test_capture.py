#!/usr/bin/env python3
"""Exercise UIWindow capture-tree limits and snapshot validation.

The C harness extracts the production capture functions from prm_uifix.c and
compiles them as a 32-bit host binary with AddressSanitizer and UBSan. Fixture
objects use the native DWORD pointer layout (parent at +0x10, child list head
at +0x50, and list nodes next/prev/child at +0/+4/+8). ``--tree-only`` omits
the snapshot tests so the same boundary tests can be run against the previous
release source; that mode is expected to expose the old exact-512 and
pending-work truncation behavior.
"""

import argparse
import os
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True

from test_input import extract_function


ROOT = Path(__file__).resolve().parent


def extract_type(source, name):
    marker = "} " + name + ";"
    end = source.find(marker)
    if end < 0:
        raise RuntimeError(f"missing production type {name}")
    start = source.rfind("typedef struct {", 0, end)
    if start < 0:
        raise RuntimeError(f"missing production typedef for {name}")
    return source[start:end + len(marker)]


def extract_constant(source, name):
    marker = "#define " + name
    for line in source.splitlines():
        if line.startswith(marker + " ") or line.startswith(marker + "\t"):
            return line + "\n"
    raise RuntimeError(f"missing production constant {name}")


PREFIX = r'''
#include <assert.h>
#include <stdint.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
typedef uint8_t BYTE;
typedef int32_t LONG;
typedef uint16_t WORD;
typedef uint32_t DWORD;
typedef uintptr_t ULONG_PTR;
typedef struct { float l,t,r,b; } UIRectF;
'''


STUBS = r'''
#define MAX_OWNER_WINDOWS 64

static OwnerCaptureLink g_owner_capture_build[MAX_OWNER_CAPTURE_LINKS];
static DWORD g_owner_capture_build_count;
static DWORD g_owner_capture_link_overflow;
static DWORD g_owner_capture_capacity_limits;
static DWORD g_owner_capture_walk_limits;
static DWORD g_owner_capture_stale_roots;
static DWORD g_owner_capture_link_peak;
static DWORD g_ui_present_serial;
static int g_owner_bitmap_hooks_installed;
static OwnerWindowState g_owner_windows[MAX_OWNER_WINDOWS];
static DWORD g_owner_window_count;

static unsigned int g_log_count;
static void s_append(char *dst, unsigned int cap, const char *src) {
    unsigned int i=0, j=0;
    if(!dst || !cap || !src) return;
    while(i+1<cap && dst[i]) ++i;
    while(i+1<cap && src[j]) dst[i++]=src[j++];
    if(i<cap) dst[i]=0;
}
static void s_append_uint(char *dst, unsigned int cap, DWORD value) {
    char temp[16]; unsigned int n=0;
    if(!dst || !cap) return;
    if(!value) { s_append(dst,cap,"0"); return; }
    while(value && n<sizeof(temp)) { temp[n++]=(char)('0'+value%10); value/=10; }
    while(n) { char one[2]={temp[--n],0}; s_append(dst,cap,one); }
}
static void s_append_hex8(char *dst, unsigned int cap, DWORD value) {
    static const char digits[]="0123456789abcdef";
    char temp[9]; unsigned int i;
    for(i=0;i<8;++i) temp[7-i]=digits[(value>>(i*4))&15];
    temp[8]=0; s_append(dst,cap,temp);
}
static void log_line(const char *line) { (void)line; ++g_log_count; }

/* Only these explicitly registered fixture ranges are readable. Invalid and
   stale DWORDs therefore fail before the extracted production code can
   dereference them. */
typedef struct { uintptr_t base; size_t size; } ReadRange;
#define MAX_READ_RANGES 8
static ReadRange g_ranges[MAX_READ_RANGES];
static unsigned int g_range_count;
static void permit_range(const void *base, size_t size) {
    assert(g_range_count<MAX_READ_RANGES);
    g_ranges[g_range_count++]=(ReadRange){(uintptr_t)base,size};
}
static int mem_readable(const void *p, DWORD bytes) {
    uintptr_t q=(uintptr_t)p; unsigned int i;
    if(!p || !bytes) return 0;
    for(i=0;i<g_range_count;++i) {
        uintptr_t end=g_ranges[i].base+g_ranges[i].size;
        if(q>=g_ranges[i].base && q<=end && (uintptr_t)bytes<=end-q) return 1;
    }
    return 0;
}
static int s_equal(const char *a, const char *b) {
    return a && b && strcmp(a,b)==0;
}
static int s_contains(const char *a, const char *b) {
    return a && b && strstr(a,b)!=0;
}
'''


TESTS = r'''
#define MAX_FIXTURE_WINDOWS 5000
#define MAX_FIXTURE_NODES 5000
typedef struct { BYTE bytes[0x54]; } WindowFixture;
typedef struct { DWORD next,prev; } HeadFixture;
typedef struct { DWORD next,prev,child; } NodeFixture;
static WindowFixture windows[MAX_FIXTURE_WINDOWS];
static HeadFixture heads[MAX_FIXTURE_WINDOWS];
static NodeFixture nodes[MAX_FIXTURE_NODES];
static unsigned int fixture_window_count,fixture_node_count;

static DWORD ptr32(const void *p) {
    uintptr_t value=(uintptr_t)p;
    assert(value<=UINT32_MAX);
    return (DWORD)value;
}
static DWORD read_word(const void *base, size_t offset) {
    DWORD value;
    memcpy(&value,(const BYTE*)base+offset,sizeof(value));
    return value;
}
static void write_word(void *base, size_t offset, DWORD value) {
    memcpy((BYTE*)base+offset,&value,sizeof(value));
}
static void fixture_init(unsigned int count) {
    unsigned int i;
    assert(count<=MAX_FIXTURE_WINDOWS);
    memset(windows,0,sizeof(windows));
    memset(heads,0,sizeof(heads));
    memset(nodes,0,sizeof(nodes));
    fixture_window_count=count; fixture_node_count=0;
    g_range_count=0;
    permit_range(windows,sizeof(windows));
    permit_range(heads,sizeof(heads));
    permit_range(nodes,sizeof(nodes));
    for(i=0;i<count;++i) {
        windows[i].bytes[0]=0;
        write_word(windows[i].bytes,0,0x70000000UL+i);
        write_word(windows[i].bytes,0x50,ptr32(&heads[i]));
        heads[i].next=ptr32(&heads[i]); heads[i].prev=ptr32(&heads[i]);
    }
}
static void reset_build(void) {
    memset(g_owner_capture_build,0,sizeof(g_owner_capture_build));
    g_owner_capture_build_count=0;
    g_owner_capture_link_overflow=0;
    g_owner_capture_capacity_limits=0;
    g_owner_capture_walk_limits=0;
    g_owner_capture_stale_roots=0;
    g_owner_capture_link_peak=0;
    g_owner_bitmap_hooks_installed=1;
    g_owner_window_count=0;
    g_ui_present_serial=100;
    g_log_count=0;
}
static void add_children(unsigned int parent, unsigned int first, unsigned int count) {
    unsigned int i;
    HeadFixture *head=&heads[parent];
    assert(first+count<=fixture_window_count);
    assert(fixture_node_count+count<=MAX_FIXTURE_NODES);
    head->next=count ? ptr32(&nodes[fixture_node_count]) : ptr32(head);
    head->prev=count ? ptr32(&nodes[fixture_node_count+count-1]) : ptr32(head);
    for(i=0;i<count;++i) {
        unsigned int node_index=fixture_node_count+i;
        NodeFixture *node=&nodes[node_index];
        WindowFixture *child=&windows[first+i];
        write_word(child->bytes,0x10,ptr32(&windows[parent]));
        node->prev=(i ? ptr32(&nodes[node_index-1]) : ptr32(head));
        node->next=(i+1<count ? ptr32(&nodes[node_index+1]) : ptr32(head));
        node->child=ptr32(child);
    }
    fixture_node_count+=count;
}
static void make_chain(unsigned int count) {
    unsigned int i;
    fixture_init(count);
    for(i=0;i+1<count;++i) add_children(i,i+1,1);
}
static int has_link(DWORD object, DWORD root) {
    unsigned int i;
    for(i=0;i<g_owner_capture_build_count;++i)
        if(g_owner_capture_build[i].object_ptr==object && g_owner_capture_build[i].root_owner==root) return 1;
    return 0;
}
static void state_root(unsigned int index, unsigned int window, const char *name,
                       DWORD bitmap_present, int matching_vtable) {
    OwnerWindowState *state=&g_owner_windows[index];
    memset(state,0,sizeof(*state));
    state->object_ptr=ptr32(&windows[window]);
    state->vtable_ptr=read_word(windows[window].bytes,0);
    if(!matching_vtable) state->vtable_ptr^=0x1000UL;
    state->bitmap_present=bitmap_present;
    strncpy(state->class_name,name,sizeof(state->class_name)-1);
    state->class_name[sizeof(state->class_name)-1]=0;
    if(g_owner_window_count<=index) g_owner_window_count=index+1;
}
static void state_invalid_root(unsigned int index, DWORD object, const char *name,
                               DWORD bitmap_present) {
    OwnerWindowState *state=&g_owner_windows[index];
    memset(state,0,sizeof(*state));
    state->object_ptr=object; state->vtable_ptr=0x12345678UL;
    state->bitmap_present=bitmap_present;
    strncpy(state->class_name,name,sizeof(state->class_name)-1);
    state->class_name[sizeof(state->class_name)-1]=0;
    if(g_owner_window_count<=index) g_owner_window_count=index+1;
}
static void test_nested_parent_filter(void) {
    DWORD root,child,grandchild,wrong;
    reset_build(); fixture_init(5);
    add_children(0,1,2); /* windows 1 and 2; window 2 has a wrong parent below. */
    add_children(1,3,1); /* valid nesting: root -> child -> grandchild */
    write_word(windows[2].bytes,0x10,ptr32(&windows[4]));
    root=ptr32(&windows[0]); child=ptr32(&windows[1]);
    grandchild=ptr32(&windows[3]); wrong=ptr32(&windows[2]);
    owner_capture_build_tree(root);
    assert(g_owner_capture_build_count==3);
    assert(has_link(root,root) && has_link(child,root) && has_link(grandchild,root));
    assert(!has_link(wrong,root));
    assert(g_owner_capture_link_overflow==0 && g_owner_capture_walk_limits==0);
    puts("PASS: nested descendants are copied and wrong-parent list entries are filtered");
}
static void test_sibling_boundary(void) {
    reset_build(); fixture_init(513); add_children(0,1,512);
    owner_capture_build_tree(ptr32(&windows[0]));
    assert(g_owner_capture_build_count==513);
    assert(g_owner_capture_link_overflow==0 && g_owner_capture_walk_limits==0);
    reset_build(); fixture_init(514); add_children(0,1,513);
    owner_capture_build_tree(ptr32(&windows[0]));
    assert(g_owner_capture_build_count==513);
    assert(g_owner_capture_link_overflow==1 && g_owner_capture_walk_limits==1);
    assert(g_owner_capture_capacity_limits==0);
    puts("PASS: exactly 512 siblings complete; the 513th is a recorded walk limit");
}
static void test_malformed_cycle(void) {
    DWORD root,child;
    reset_build(); fixture_init(2); add_children(0,1,1);
    root=ptr32(&windows[0]); child=ptr32(&windows[1]);
    nodes[0].next=ptr32(&nodes[0]); /* malformed list never reaches its head */
    owner_capture_build_tree(root);
    assert(g_owner_capture_build_count==2 && has_link(child,root));
    assert(g_owner_capture_walk_limits==1 && g_owner_capture_link_overflow==1);
    puts("PASS: malformed cyclic list is bounded and records its sibling walk limit");
}
static void test_alias_capacity(void) {
    reset_build(); make_chain(4096);
    owner_capture_build_tree(ptr32(&windows[0]));
    assert(g_owner_capture_build_count==4096);
    assert(g_owner_capture_link_overflow==0 && g_owner_capture_capacity_limits==0);
    reset_build(); make_chain(4097);
    owner_capture_build_tree(ptr32(&windows[0]));
    assert(g_owner_capture_build_count==4096);
    assert(g_owner_capture_link_overflow==1 && g_owner_capture_capacity_limits==1);
    assert(g_owner_capture_walk_limits==0);
    puts("PASS: 4096 aliases fit; the 4097th records a genuine alias capacity limit");
}
static void test_limit_log_budget(void) {
    unsigned int i;
    reset_build(); fixture_init(1);
    for(i=0;i<6;++i) owner_capture_note_limit((i%3)+1,1,2,3);
    assert(g_owner_capture_link_overflow==6);
    assert(g_owner_capture_capacity_limits==4 && g_owner_capture_walk_limits==2);
    assert(g_log_count==4);
    puts("PASS: limit counters distinguish capacity/walk kinds and cap diagnostic logging at four");
}
static void test_snapshot_validation(void) {
    DWORD root;
    reset_build(); fixture_init(4); add_children(0,1,1);
    root=ptr32(&windows[0]);
    state_root(0,0,"UIItemWnd",98,1); /* age two is still recent */
    g_ui_present_serial=100;
    owner_capture_build_snapshot();
    assert(g_owner_capture_build_count==2 && has_link(root,root));
    assert(g_owner_capture_link_peak==2 && g_owner_capture_stale_roots==0);

    reset_build(); fixture_init(3); add_children(0,1,1);
    state_root(0,0,"UIItemWnd",97,1); /* age three is stale */
    g_ui_present_serial=100; owner_capture_build_snapshot();
    assert(g_owner_capture_build_count==0 && g_owner_capture_stale_roots==0);

    reset_build(); fixture_init(3); add_children(0,1,1);
    state_invalid_root(0,0xdead1234UL,"UIItemWnd",100);
    g_ui_present_serial=100; owner_capture_build_snapshot();
    assert(g_owner_capture_build_count==0 && g_owner_capture_stale_roots==1);
    /* A readable object with a changed vtable is a reused root, and must also
       be rejected before its valid child list is traversed. */
    reset_build(); fixture_init(3); add_children(0,1,1);
    state_root(0,0,"UIItemWnd",100,0);
    owner_capture_build_snapshot();
    assert(g_owner_capture_build_count==0 && g_owner_capture_stale_roots==1);
    puts("PASS: recent snapshots build; stale, unreadable, and reused roots stop before child traversal");
}
static void test_snapshot_wrap_and_filters(void) {
    reset_build(); fixture_init(1);
    state_root(0,0,"UIItemWnd",UINT32_MAX,1);
    g_ui_present_serial=1; owner_capture_build_snapshot();
    assert(g_owner_capture_build_count==1 && g_owner_capture_stale_roots==0);

    reset_build(); fixture_init(1);
    state_root(0,0,"UIItemWnd",100,1); g_ui_present_serial=100;
    g_owner_bitmap_hooks_installed=0; owner_capture_build_snapshot();
    assert(g_owner_capture_build_count==0 && g_owner_capture_link_peak==0);

    reset_build(); fixture_init(2); add_children(0,1,1);
    state_root(0,0,"ToolTipWnd",100,1);
    state_root(1,0,"CSignBoardWnd",100,1);
    state_root(2,0,"UINameBalloonText",100,1);
    state_root(3,0,"UIVerticalNameBalloonText",100,1);
    owner_capture_build_snapshot();
    assert(g_owner_capture_build_count==0 && g_owner_capture_link_peak==0);
    assert(g_owner_capture_stale_roots==0);
    /* Add an active root in a fresh snapshot. Its object identity deliberately
       matches the passive fixtures, so the preceding zero-result is the only
       evidence that all passive roots were skipped. */
    reset_build(); fixture_init(2); add_children(0,1,1);
    state_root(0,0,"UIItemWnd",100,1);
    owner_capture_build_snapshot();
    assert(g_owner_capture_build_count==2 && g_owner_capture_link_peak==2);
    puts("PASS: unsigned present wraparound works; disabled hooks and popup/NPC/hover-name roots are skipped");
}
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=ROOT / "prm_uifix.c")
    parser.add_argument("--tree-only", action="store_true",
                        help="run tree boundary tests without snapshot extraction")
    parser.add_argument("--case", choices=("all", "siblings", "capacity"), default="all",
                        help="run all tests or one focused tree-boundary case")
    args = parser.parse_args()
    source = args.source.read_text()

    types = "\n".join(extract_type(source, name)
                         for name in ("OwnerWindowState", "OwnerCaptureLink"))
    limits = extract_constant(source, "MAX_OWNER_CAPTURE_LINKS")
    tree = extract_function(source, "owner_capture_build_tree")
    pieces = [extract_function(source, name) for name in (
        "owner_class_is_hover_popup", "owner_class_is_world_label",
    )]
    if "static int owner_class_is_world_name(" in source:
        pieces.append(extract_function(source, "owner_class_is_world_name"))
    if "owner_capture_note_limit" in tree:
        pieces.append(extract_function(source, "owner_capture_note_limit"))
    pieces.append(tree)
    if not args.tree_only and args.case == "all":
        pieces.append(extract_function(source, "owner_capture_build_snapshot"))
        finalize = extract_function(source, "owner_finalize_frame")
        if "owner_capture_build_snapshot();" not in finalize:
            raise RuntimeError("owner_finalize_frame does not call capture snapshot helper")
        if ("for(i=0;i<g_owner_capture_build_count;++i) g_owner_capture_links[i]="
                not in finalize):
            raise RuntimeError("owner_finalize_frame no longer publishes the capture copy")

    # The source globals are deliberately replaced by harness globals above;
    # only the actual function bodies are compiled and exercised.
    if args.case == "all":
        tests = TESTS if not args.tree_only else TESTS[:TESTS.index("static void test_limit_log_budget")]
        calls = ("test_nested_parent_filter(); test_sibling_boundary(); "
                 "test_malformed_cycle(); test_alias_capacity(); "
                 "test_limit_log_budget(); test_snapshot_validation(); "
                 "test_snapshot_wrap_and_filters();")
        if args.tree_only:
            calls = ("test_nested_parent_filter(); test_sibling_boundary(); "
                     "test_malformed_cycle(); test_alias_capacity();")
    elif args.case == "siblings":
        tests = TESTS[:TESTS.index("static void test_limit_log_budget")]
        calls = "test_sibling_boundary();"
    else:
        tests = TESTS[:TESTS.index("static void test_limit_log_budget")]
        calls = "test_alias_capacity();"
    tests += "\nint main(void) { " + calls + " return 0; }\n"
    text = PREFIX + types + "\n" + limits + STUBS + "\n".join(pieces) + tests

    with tempfile.TemporaryDirectory(prefix="prm-capture-test-") as directory:
        directory_path = Path(directory)
        harness = directory_path / "capture.c"
        binary = directory_path / "capture-test"
        harness.write_text(text)
        compiler = shlex.split(os.environ.get("CC", "clang"))
        flags = ["-m32", "-std=c11", "-O1", "-g", "-Wall", "-Wextra", "-Werror",
                 "-fsanitize=address,undefined", "-fno-sanitize-recover=all",
                 "-fno-omit-frame-pointer", str(harness), "-o", str(binary)]
        if args.tree_only or args.case != "all":
            # Focused/tree-only modes leave snapshot-only or other test stubs
            # unused; production tree functions remain compiled with Werror.
            flags.insert(flags.index(str(harness)), "-Wno-unused-function")
        subprocess.run(compiler + flags, check=True)
        env = os.environ.copy()
        env.setdefault("ASAN_OPTIONS", "detect_leaks=0")
        subprocess.run([str(binary)], check=True, env=env)
    mode = "tree-only" if args.tree_only else "snapshot+tree"
    print(f"PASS: extracted capture {mode}/{args.case} functions with 32-bit ASan/UBSan host fixtures")


if __name__ == "__main__":
    main()
