#!/usr/bin/env python3
"""Run native tests of the actual input functions extracted from prm_uifix.c.

These stubbed API tests cover coordinate handling, not Windows hook execution.
The thiscall attribute is removed only for the native test build; validate PE
callsites separately with verify_hooks.py.
"""

import argparse
import os
from pathlib import Path
import re
import shlex
import subprocess
import tempfile


FUNCTIONS = ("input_read_raw_point", "world_scale_coord", "world_ray_scoped", "cursor_raw_coord")


def extract_function(source, name):
    start = re.search(r"^static [^\n]*\b" + re.escape(name) + r"\s*\(", source, re.M)
    if not start:
        raise ValueError(f"missing actual source function {name}")
    opening = source.index("{", start.start())
    tokens = re.finditer(r'/\*.*?\*/|//[^\n]*|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|[{}]', source[opening:], re.S)
    depth = 0
    for token in tokens:
        if token[0] == "{":
            depth += 1
        elif token[0] == "}":
            depth -= 1
            if depth == 0:
                function = source[start.start():opening + token.end()]
                return function.replace("__attribute__((thiscall))", "")
    raise ValueError(f"unterminated actual source function {name}")


STUBS = r'''
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
typedef int32_t LONG;
typedef uint32_t DWORD;
typedef uint8_t BYTE;
typedef uint32_t HWND;
typedef struct { LONG x,y; } POINT;
typedef struct { LONG left,top,right,bottom; } RECT;
static HWND g_input_hwnd=7;
static BYTE* g_exe;
static DWORD g_exe_size;
static int readable=1, cursor_ok=1, conversion_ok=1, rectangle_ok=1;
static int cursor_queries, conversion_queries, rectangle_queries;
static POINT screen={1820,770}, origin={100,50};
static RECT actual_client={0,0,3440,1440};
static int mem_readable(const void* p, DWORD n) { (void)p; (void)n; return readable; }
static int fake_cursor(POINT* p) { ++cursor_queries; *p=screen; return cursor_ok; }
static int fake_convert(HWND hwnd, POINT* p) {
    assert(hwnd==7); ++conversion_queries;
    p->x-=origin.x; p->y-=origin.y; return conversion_ok;
}
static int fake_rectangle(HWND hwnd, RECT* r) {
    assert(hwnd==7); ++rectangle_queries; *r=actual_client; return rectangle_ok;
}
static int (*g_GetCursorPos)(POINT*)=fake_cursor;
static int (*g_real_ScreenToClient)(HWND,POINT*)=fake_convert;
static int (*g_GetClientRect)(HWND,RECT*)=fake_rectangle;
static int g_world_input_enabled=1, g_world_input_normalize=1;
static LONG g_world_raw_x,g_world_raw_y,g_world_mapped_x,g_world_mapped_y;
static DWORD g_world_input_calls,g_world_input_raw_uses,g_world_input_normalized;
static DWORD g_world_input_raw_failures,g_world_input_max_delta;
static LONG g_world_input_view_w,g_world_input_view_h;
static LONG g_world_input_client_w,g_world_input_client_h;
static int g_world_input_dims_logged;
static void s_append(char* s, unsigned int n, const char* a) { (void)s;(void)n;(void)a; }
static void s_append_int(char* s, unsigned int n, LONG a) { (void)s;(void)n;(void)a; }
static void log_line(const char* s) { (void)s; }
static int forwarded;
static LONG forwarded_x,forwarded_y;
static void *forwarded_self,*forwarded_a,*forwarded_b,*forwarded_out;
static void fake_ray(void* self, LONG x, LONG y, void* a, void* b, void* out) {
    ++forwarded; forwarded_self=self; forwarded_x=x; forwarded_y=y;
    forwarded_a=a; forwarded_b=b; forwarded_out=out;
}
static void (*g_world_ray)(void*,LONG,LONG,void*,void*,void*)=fake_ray;
'''


TESTS = r'''
static void assert_point(POINT p, LONG x, LONG y) { assert(p.x==x); assert(p.y==y); }
static void test_raw(void) {
    POINT out={11,22}; RECT client={1,2,3,4};
    cursor_ok=0;
    assert(!input_read_raw_point(&out,&client)); assert_point(out,11,22);
    assert(client.left==1 && client.bottom==4 && conversion_queries==0);
    cursor_ok=1; conversion_ok=0;
    assert(!input_read_raw_point(&out,&client)); assert_point(out,11,22);
    assert(client.left==1 && client.bottom==4);
    conversion_ok=1;
    assert(input_read_raw_point(&out,&client)); assert_point(out,1720,720);
    assert(client.right==3440 && client.bottom==1440);
    int before=cursor_queries;
    for(int i=0;i<100;++i) {
        assert(input_read_raw_point(&out,0)); assert_point(out,1720,720);
    }
    assert(cursor_queries-before==100); /* stationary samples are freshly queried */
    rectangle_ok=0;
    assert(input_read_raw_point(&out,&client)); assert_point(out,1720,720);
    assert(client.left==0 && client.top==0 && client.right==0 && client.bottom==0);
    rectangle_ok=1;
    screen.x=40000;
    assert(!input_read_raw_point(&out,&client)); assert_point(out,1720,720);
    screen.x=1820;
    g_GetCursorPos=0;
    assert(!input_read_raw_point(&out,0)); assert_point(out,1720,720);
    g_GetCursorPos=fake_cursor;
    g_real_ScreenToClient=0;
    assert(!input_read_raw_point(&out,0)); assert_point(out,1720,720);
    g_real_ScreenToClient=fake_convert;
    g_input_hwnd=0;
    assert(!input_read_raw_point(&out,0)); assert_point(out,1720,720);
    g_input_hwnd=7;
    puts("PASS: API failures do not commit partial points; stationary queries refresh; missing dimensions remain unavailable");
}
static void test_scale(void) {
    const LONG values[]={-32768,-1720,-1,0,1,1720,32768};
    for(unsigned int i=0;i<sizeof(values)/sizeof(values[0]);++i)
        assert(world_scale_coord(values[i],3440,3440)==values[i]);
    assert(world_scale_coord(860,3440,1720)==1720);
    assert(world_scale_coord(-860,3440,1720)==-1720);
    assert(world_scale_coord(1,1,2)==1);
    assert(world_scale_coord(-1,1,2)==-1);
    assert(world_scale_coord(32768,16384,1)==536870912);
    assert(world_scale_coord(-32768,16384,1)==-536870912);
    assert(world_scale_coord(32769,2,1)==32769);
    assert(world_scale_coord(-32769,2,1)==-32769);
    assert(world_scale_coord(5,0,1)==5);
    assert(world_scale_coord(5,1,0)==5);
    assert(world_scale_coord(5,16385,1)==5);
    assert(world_scale_coord(5,1,16385)==5);
    assert(cursor_raw_coord(203,900,200)==903);
    assert(cursor_raw_coord(193,900,200)==893);
    assert(cursor_raw_coord(-12,-100,-10)==-102);
    assert(cursor_raw_coord(65537,900,200)==65537);
    assert(cursor_raw_coord(203,32769,200)==203);
    assert(cursor_raw_coord(203,900,-32769)==203);
    puts("PASS: signed scale identity, differing sizes, limits, rounding, and cursor hotspot offsets");
}
static void test_ray(void) {
    uint32_t renderer[16]={0}; int camera_a=1,camera_b=2,out=3;
    renderer[0x24/4]=3440; renderer[0x28/4]=1440;
    renderer[0x2c/4]=1720; renderer[0x30/4]=720;
    world_ray_scoped(renderer,123,456,&camera_a,&camera_b,&out);
    assert(forwarded==1 && forwarded_self==renderer);
    assert(forwarded_a==&camera_a && forwarded_b==&camera_b && forwarded_out==&out);
    assert(forwarded_x==1720 && forwarded_y==720); /* halves would yield 860,360 */
    const POINT corners[]={{0,0},{3439,0},{0,1439},{3439,1439}};
    for(unsigned int i=0;i<4;++i) {
        screen.x=corners[i].x+origin.x; screen.y=corners[i].y+origin.y;
        world_ray_scoped(renderer,123,456,0,0,0);
        assert(forwarded_x==corners[i].x && forwarded_y==corners[i].y);
    }
    actual_client.right=1720; actual_client.bottom=720;
    screen.x=960; screen.y=410;
    world_ray_scoped(renderer,123,456,0,0,0);
    assert(forwarded_x==1720 && forwarded_y==720 && g_world_input_normalized==1);
    screen.x=0; screen.y=0;
    world_ray_scoped(renderer,123,456,0,0,0);
    assert(forwarded_x==-200 && forwarded_y==-100);
    screen.x=960; screen.y=410;
    conversion_ok=0;
    world_ray_scoped(renderer,777,888,0,0,0);
    assert(forwarded_x==777 && forwarded_y==888 && g_world_input_raw_failures==1);
    conversion_ok=1; rectangle_ok=0;
    world_ray_scoped(renderer,777,888,0,0,0);
    assert(forwarded_x==860 && forwarded_y==360); /* cannot normalize without client dimensions */
    rectangle_ok=1; g_world_input_normalize=0;
    world_ray_scoped(renderer,777,888,0,0,0);
    assert(forwarded_x==860 && forwarded_y==360);
    g_world_input_normalize=1; g_world_input_enabled=0;
    int before=cursor_queries;
    world_ray_scoped(renderer,777,888,0,0,0);
    assert(forwarded_x==777 && forwarded_y==888 && cursor_queries==before);
    g_world_input_enabled=1; readable=0;
    world_ray_scoped(renderer,777,888,0,0,0);
    assert(forwarded_x==860 && forwarded_y==360); /* must not use the previous renderer dimensions */
    readable=1;
    world_ray_scoped(0,777,888,0,0,0);
    assert(forwarded_x==860 && forwarded_y==360);
    world_ray_scoped(renderer,INT32_MIN,INT32_MAX,0,0,0);
    assert(forwarded_x==1720 && forwarded_y==720);
    assert(g_world_input_max_delta==UINT32_C(2147485368));
    puts("PASS: actual ray wrapper forwards raw/full-viewport coordinates and preserves input on failure or disable");
}
int main(void) { test_raw(); test_scale(); test_ray(); return 0; }
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=Path(__file__).resolve().with_name("prm_uifix.c"))
    args = parser.parse_args()
    source = args.source.read_text()
    constant = re.search(r"^#define\s+PRM_MAIN_HWND_RVA\s+[^\n]+", source, re.M)
    if not constant:
        raise ValueError("missing source PRM_MAIN_HWND_RVA")
    code = constant[0] + "\n" + STUBS + "\n".join(extract_function(source, name) for name in FUNCTIONS) + TESTS
    with tempfile.TemporaryDirectory(prefix="prm-input-test-") as directory:
        harness = Path(directory) / "input.c"
        binary = Path(directory) / "input-test"
        harness.write_text(code)
        compiler = shlex.split(os.environ.get("CC", "clang"))
        subprocess.run(compiler + ["-std=c11", "-O1", "-g", "-Wall", "-Wextra", "-Werror",
                                   "-fsanitize=undefined", "-fno-sanitize-recover=all", str(harness), "-o", str(binary)], check=True)
        subprocess.run([str(binary)], check=True)
    print("PASS: native extracted-function tests (stub APIs; no Windows integration claim)")


if __name__ == "__main__":
    main()
