#!/usr/bin/env python3
"""Exercise the production cursor registry with host ASan/UBSan.

Extracts the actual C registry and coordinate helper; does not model the
Windows wrappers or claim to validate native rendering visually.
"""

from pathlib import Path
import os
import re
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parent
source = (ROOT / "prm_uifix.c").read_text()


def function(name):
    match = re.search(r"^static [^\n]*\b" + re.escape(name) + r"\([^;]*?\)\s*\{", source, re.M)
    if not match:
        raise RuntimeError(f"Cannot extract production function: {name}")
    depth = 1
    end = match.end()
    while depth:
        depth += (source[end] == "{") - (source[end] == "}")
        end += 1
    return source[match.start():end]


globals_start = source.index("#define MAX_CURSOR_DRAWS ")
globals_end = source.index("\n\n/*", globals_start)
production = source[globals_start:globals_end] + "\n" + "\n".join(
    function(name) for name in (
        "cursor_registry_lock", "cursor_registry_unlock", "cursor_note_vertices",
        "cursor_consume_vertices", "cursor_raw_coord",
    )
)

prefix = r"""
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
typedef uint32_t DWORD;
typedef int32_t LONG;
typedef unsigned char BYTE;
static DWORD g_ui_present_serial;
static const void* unreadable;
static int mem_readable(const void* p, DWORD n) {
    return p && p != unreadable && n <= 128;
}
#define CHECK(x) do { if (!(x)) { \
    fprintf(stderr,"check failed at line %d: %s\n", __LINE__, #x); exit(1); \
} } while (0)
"""

tests = r"""
static void reset(void) {
    memset(g_cursor_draws, 0, sizeof(g_cursor_draws));
    g_cursor_draw_lock=0; g_ui_present_serial=100;
    g_cursor_submits=g_cursor_bypassed=g_cursor_overflow=0;
    g_cursor_expired=g_cursor_mismatched=g_cursor_peak=0;
    unreadable=0;
}
static void make_vertices(DWORD v[4][8], DWORD seed) {
    DWORD i,j;
    for(i=0;i<4;++i) for(j=0;j<8;++j) v[i][j]=seed+i*8+j;
}
static void identity(void) {
    DWORD a[4][8], b[4][8];
    reset(); make_vertices(a,1000); memcpy(b,a,sizeof(b));
    CHECK(!cursor_consume_vertices(0x1c4,a,4));
    cursor_note_vertices(a,4,1);
    CHECK(!cursor_consume_vertices(0x1c4,b,4)); /* equal content, different allocation */
    CHECK(cursor_consume_vertices(0x1c4,a,4));
    CHECK(!cursor_consume_vertices(0x1c4,a,4)); /* one consumption */
    CHECK(g_cursor_submits==1 && g_cursor_bypassed==1 && g_cursor_peak==1);
}
static void fingerprint(void) {
    DWORD a[4][8],i,j; const DWORD fields[]={0,1,2,3,6,7};
    for(i=0;i<4;++i) for(j=0;j<6;++j) {
        reset(); make_vertices(a,2000); cursor_note_vertices(a,4,1);
        a[i][fields[j]]^=1;
        CHECK(!cursor_consume_vertices(0x1c4,a,4));
        CHECK(g_cursor_mismatched==1);
        a[i][fields[j]]^=1;
        CHECK(!cursor_consume_vertices(0x1c4,a,4)); /* mismatch consumes stale tag */
    }
    reset(); make_vertices(a,2000); cursor_note_vertices(a,4,1);
    for(i=0;i<4;++i) { a[i][4]^=0xffffffff; a[i][5]^=0xffffffff; }
    CHECK(cursor_consume_vertices(0x1c4,a,4)); /* native color/specular changes are allowed */
}
static void invalidation(void) {
    DWORD a[4][8];
    reset(); make_vertices(a,3000);
    cursor_note_vertices(a,4,1); cursor_note_vertices(a,4,0);
    CHECK(!cursor_consume_vertices(0x1c4,a,4));
    cursor_note_vertices(a,4,1); cursor_note_vertices(a,3,1);
    CHECK(!cursor_consume_vertices(0x1c4,a,4));
    CHECK(g_cursor_mismatched==1);
    cursor_note_vertices(a,4,1);
    unreadable=a; cursor_note_vertices(a,4,1); unreadable=0;
    CHECK(!cursor_consume_vertices(0x1c4,a,4));
    CHECK(g_cursor_mismatched==2);
    cursor_note_vertices(a,4,1);
    CHECK(!cursor_consume_vertices(0x2c4,a,4));
    CHECK(!cursor_consume_vertices(0x1c4,a,4));
    cursor_note_vertices(a,4,1);
    CHECK(!cursor_consume_vertices(0x1c4,a,3));
    cursor_note_vertices(a,4,1); make_vertices(a,4000); cursor_note_vertices(a,4,1);
    CHECK(cursor_consume_vertices(0x1c4,a,4)); /* new tag replaces the pooled allocation */
    CHECK(g_cursor_peak==1);
}
static void lifetime(void) {
    DWORD a[4][8],b[4][8];
    reset(); make_vertices(a,5000); make_vertices(b,6000);
    cursor_note_vertices(a,4,1); g_ui_present_serial+=2;
    CHECK(cursor_consume_vertices(0x1c4,a,4)); /* two-boundary grace remains valid */
    cursor_note_vertices(a,4,1); g_ui_present_serial+=3;
    CHECK(!cursor_consume_vertices(0x1c4,a,4));
    CHECK(g_cursor_expired==1);
    cursor_note_vertices(a,4,1); g_ui_present_serial+=3; cursor_note_vertices(b,4,1);
    CHECK(g_cursor_expired==2); /* note path also prunes */
    CHECK(!cursor_consume_vertices(0x1c4,a,4));
    CHECK(cursor_consume_vertices(0x1c4,b,4));
    reset(); g_ui_present_serial=UINT32_MAX-1; cursor_note_vertices(a,4,1);
    g_ui_present_serial=0; CHECK(cursor_consume_vertices(0x1c4,a,4));
    g_ui_present_serial=UINT32_MAX-1; cursor_note_vertices(a,4,1);
    g_ui_present_serial=1; CHECK(!cursor_consume_vertices(0x1c4,a,4));
    CHECK(g_cursor_expired==1); /* unsigned age survives wrap */
}
static void capacity(void) {
    DWORD a[MAX_CURSOR_DRAWS+1][4][8],i;
    reset();
    for(i=0;i<=MAX_CURSOR_DRAWS;++i) {
        make_vertices(a[i],7000+i*100); cursor_note_vertices(a[i],4,1);
    }
    CHECK(g_cursor_overflow==1 && g_cursor_peak==MAX_CURSOR_DRAWS);
    CHECK(!cursor_consume_vertices(0x1c4,a[MAX_CURSOR_DRAWS],4));
    for(i=0;i<MAX_CURSOR_DRAWS;++i) CHECK(cursor_consume_vertices(0x1c4,a[i],4));
    cursor_note_vertices(a[MAX_CURSOR_DRAWS],4,1);
    CHECK(cursor_consume_vertices(0x1c4,a[MAX_CURSOR_DRAWS],4));
}
static void coordinates(void) {
    CHECK(cursor_raw_coord(502,800,500)==802); /* retain +2 hotspot offset */
    CHECK(cursor_raw_coord(-10,-80,-8)==-82);
    CHECK(cursor_raw_coord(65537,0,0)==65537);
    CHECK(cursor_raw_coord(10,32769,5)==10);
    CHECK(cursor_raw_coord(10,5,-32769)==10);
    CHECK(cursor_raw_coord(65536,32768,-32768)==131072);
}
int main(void) {
    identity(); fingerprint(); invalidation(); lifetime(); capacity(); coordinates();
    puts("PASS cursor registry: identity, 24 immutable fields, colors, reuse, consume, expiry, wrap, capacity, coordinates");
    return 0;
}
"""

with tempfile.TemporaryDirectory(prefix="prm-cursor-test-") as directory:
    c_file = Path(directory) / "cursor_test.c"
    binary = Path(directory) / "cursor_test"
    c_file.write_text(prefix + production + tests)
    subprocess.run([
        os.environ.get("CC", "clang"), "-std=c11", "-O1", "-g", "-Wall", "-Wextra",
        "-Wno-unused-variable", "-fsanitize=address,undefined", "-fno-omit-frame-pointer",
        str(c_file), "-o", str(binary),
    ], check=True)
    subprocess.run([str(binary)], check=True)
