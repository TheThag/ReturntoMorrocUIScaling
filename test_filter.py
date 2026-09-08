#!/usr/bin/env python3
"""Exercise actual UI filter scopes and draw hooks with a fake native COM device.

The scaler boundary is stubbed: its original-versus-transformed pointer result
is covered separately by test_bitmap.py. This is not a Windows rendering test.
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
from test_drag import extract_type
from test_present import definition


PREFIX = r'''
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#define WINAPI
typedef int32_t HRESULT;
typedef uint32_t DWORD;
typedef uint16_t WORD;
typedef uint8_t BYTE;
typedef uintptr_t ULONG_PTR;
'''


STUBS = r'''
static void* fake_vtable[49];
static struct { void** vt; } fake_device={fake_vtable};
static DevHookRec record;
static int absent_record;
static int g_ui_sharp_filter=1;
static DWORD g_ui_sharp_draws,g_ui_sharp_failures;
static DWORD magnification=2,minification=2;
static int get_count,set_count,draw_count,scale_count;
static DWORD get_failure,set_failure;
static DWORD restore_failure;
static int failed_set_mutates;
static int transformed=1;
static HRESULT draw_result;
static DWORD expected_mag,expected_min;
static int indexed;
static BYTE vertices[128],transformed_vertices[128];
static WORD indices[6]={0,1,2,0,2,3};
static DevHookRec* dev_rec(void* self) {
    assert(self==&fake_device); return absent_record?0:&record;
}
static HRESULT fake_get(void* self,DWORD stage,DWORD state,DWORD* value) {
    assert(self==&fake_device && stage==0 && (state==16 || state==17));
    ++get_count;
    if(state==get_failure) return (HRESULT)0x80004005U;
    *value=state==16?magnification:minification;
    return 0;
}
static HRESULT fake_set(void* self,DWORD stage,DWORD state,DWORD value) {
    assert(self==&fake_device && stage==0 && (state==16 || state==17));
    ++set_count;
    if(state==set_failure && value==1) {
        if(failed_set_mutates) {
            if(state==16) magnification=value; else minification=value;
        }
        return (HRESULT)0x80004005U;
    }
    if(state==restore_failure && value!=1) return (HRESULT)0x80004005U;
    if(state==16) magnification=value; else minification=value;
    return 0;
}
static void assert_draw(void* self,DWORD prim,DWORD fvf,const void* v,DWORD n,DWORD flags) {
    assert(self==&fake_device && prim==4 && fvf==0x1c4 && n==4 && flags==7);
    assert(v==(transformed?transformed_vertices:vertices));
    assert(magnification==expected_mag && minification==expected_min);
    ++draw_count;
}
static HRESULT fake_draw(void* self,DWORD prim,DWORD fvf,const void* v,DWORD n,DWORD flags) {
    assert(!indexed); assert_draw(self,prim,fvf,v,n,flags); return draw_result;
}
static HRESULT fake_draw_indexed(void* self,DWORD prim,DWORD fvf,const void* v,DWORD n,
                                 const WORD* idx,DWORD nidx,DWORD flags) {
    assert(indexed && idx==indices && nidx==6);
    assert_draw(self,prim,fvf,v,n,flags); return draw_result;
}
static const void* make_scaled_ui_vertices(DWORD prim,DWORD fvf,const void* v,DWORD n,
        BYTE* scratch,DWORD cap,void* frame,DWORD caller) {
    assert(prim==4 && fvf==0x1c4 && v==vertices && n==4 && scratch && cap==1024);
    (void)frame; (void)caller; ++scale_count;
    return transformed?transformed_vertices:vertices;
}
static DWORD ptr_to_rva(void* p) { (void)p; return 0xabcdef; }
static void maybe_toggle_ui_scale(void) {}
static void maybe_toggle_ui_input(void) {}
static void maybe_toggle_ui_sharp(void) {}
static void maybe_dump_ui_groups(void) {}
static void maybe_dump_owner_windows(void) {}
static void vtrace_poll_hotkey(void) {}
static void maybe_start_capture(void) {}
static void maybe_finish_capture(void) {}
static void add_draw_stat(DWORD method,DWORD prim,DWORD fvf,DWORD n,
                          const void* v,void* caller,void* frame) {
    assert(method==(DWORD)indexed && prim==4 && fvf==0x1c4 && n==4 && v==vertices);
    (void)caller; (void)frame;
}
'''


TESTS = r'''
static void reset(void) {
    memset(fake_vtable,0,sizeof(fake_vtable));
    fake_device.vt=fake_vtable;
    fake_vtable[36]=(void*)fake_get; fake_vtable[37]=(void*)fake_set;
    record.orig_draw=(void*)fake_draw;
    record.orig_draw_indexed=(void*)fake_draw_indexed;
    absent_record=0; g_ui_sharp_filter=1; transformed=1;
    g_ui_sharp_draws=g_ui_sharp_failures=0;
    magnification=minification=2;
    get_count=set_count=draw_count=scale_count=0;
    get_failure=set_failure=restore_failure=0; failed_set_mutates=0;
    expected_mag=expected_min=1; draw_result=42;
}
static HRESULT draw(void) {
    if(indexed) return hook_DrawIndexedPrimitive(&fake_device,4,0x1c4,vertices,4,indices,6,7);
    return hook_DrawPrimitive(&fake_device,4,0x1c4,vertices,4,7);
}
static void test_draw_scope(void) {
    reset();
    assert(draw()==42);
    assert(draw_count==1 && scale_count==1 && get_count==2 && set_count==4);
    assert(magnification==2 && minification==2 && g_ui_sharp_draws==1 && !g_ui_sharp_failures);
    draw_result=(HRESULT)0x88760868U;
    assert(draw()==draw_result && draw_count==2);
    assert(magnification==2 && minification==2 && set_count==8);

    reset(); magnification=5; minification=3; /* Restore queried state, not a hardcoded LINEAR default. */
    assert(draw()==42 && magnification==5 && minification==3 && set_count==4);

    reset(); magnification=minification=1;
    assert(draw()==42 && !set_count && get_count==2 && g_ui_sharp_draws==1);
    reset(); magnification=1;
    assert(draw()==42 && magnification==1 && minification==2 && set_count==2);
    reset(); minification=1;
    assert(draw()==42 && magnification==2 && minification==1 && set_count==2);
}
static void test_unmodified_draws(void) {
    reset(); transformed=0; expected_mag=expected_min=2;
    assert(draw()==42 && !get_count && !set_count && !g_ui_sharp_draws);
    assert(draw_count==1 && scale_count==1);
    reset(); g_ui_sharp_filter=0; expected_mag=expected_min=2;
    assert(draw()==42 && !get_count && !set_count && !g_ui_sharp_draws);

    reset(); absent_record=1;
    assert(draw()==(HRESULT)0x80004005U && !get_count && !set_count && !draw_count);
    reset(); record.orig_draw=record.orig_draw_indexed=0;
    assert(draw()==(HRESULT)0x80004005U && !get_count && !set_count && !draw_count);

    reset(); fake_vtable[36]=0; expected_mag=expected_min=2;
    assert(draw()==42 && !get_count && !set_count);
    reset(); fake_vtable[37]=0; expected_mag=expected_min=2;
    assert(draw()==42 && !get_count && !set_count);
    reset(); fake_device.vt=0; expected_mag=expected_min=2;
    assert(draw()==42 && !get_count && !set_count);
}
static void test_setup_failures(void) {
    DWORD state; int mutate;
    for(state=16;state<=17;++state) {
        reset(); get_failure=state; expected_mag=expected_min=2;
        assert(draw()==42 && !set_count && draw_count==1 && g_ui_sharp_failures==1);
        assert(!g_ui_sharp_draws && magnification==2 && minification==2);
        for(mutate=0;mutate<=1;++mutate) {
            reset(); set_failure=state; failed_set_mutates=mutate; expected_mag=expected_min=2;
            assert(draw()==42 && draw_count==1 && g_ui_sharp_failures==1 && !g_ui_sharp_draws);
            assert(magnification==2 && minification==2);
            assert(set_count==(state==16?2:4)); /* Includes restoring the attempted, failing setter. */
        }
    }
}
static void test_restore_failures(void) {
    reset(); restore_failure=16;
    assert(draw()==42 && set_count==4 && g_ui_sharp_failures==1);
    assert(magnification==1 && minification==2); /* Failed MAG restoration must not skip MIN restoration. */
    reset(); restore_failure=17;
    assert(draw()==42 && set_count==4 && g_ui_sharp_failures==1);
    assert(magnification==2 && minification==1);
}
static void test_scope_lifetime(void) {
    UIFilterScope outer,inner;
    reset();
    ui_filter_begin(&fake_device,1,&outer);
    assert(magnification==1 && minification==1 && set_count==2);
    ui_filter_begin(&fake_device,1,&inner);
    ui_filter_end(&fake_device,&inner);
    assert(magnification==1 && minification==1 && set_count==2);
    ui_filter_end(&fake_device,&outer);
    assert(magnification==2 && minification==2 && set_count==4);
    ui_filter_end(&fake_device,&outer);
    assert(set_count==4); /* End is idempotent after the scope is restored. */
    reset(); memset(&inner,0xa5,sizeof(inner));
    ui_filter_begin(0,1,&inner); ui_filter_end(0,&inner);
    assert(!get_count && !set_count);
}
int main(void) {
    for(indexed=0;indexed<=1;++indexed) {
        test_draw_scope(); test_unmodified_draws(); test_setup_failures(); test_restore_failures();
        puts(indexed?"PASS: indexed draw filter scope, state restoration, unchanged draws and failure handling":
                     "PASS: primitive draw filter scope, state restoration, unchanged draws and failure handling");
    }
    test_scope_lifetime();
    puts("PASS: nested, repeated-end and null-device filter scopes");
    return 0;
}
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=Path(__file__).resolve().with_name("prm_uifix.c"))
    args = parser.parse_args()
    source = args.source.read_text()
    types = ""
    for name in ("PFN_D3D7_DrawPrimitive", "PFN_D3D7_DrawIndexedPrimitive",
                 "PFN_D3D7_GetTextureStageState", "PFN_D3D7_SetTextureStageState"):
        match = re.search(r"^typedef[^\n]*\b" + name + r"\b[^\n]*;", source, re.M)
        if not match:
            raise ValueError(f"missing actual source typedef {name}")
        types += match[0] + "\n"
    types += "\n".join(extract_type(source, name) for name in ("DevHookRec", "UIFilterScope"))
    production = "\n".join(definition(source, name) for name in (
        "ui_filter_end", "ui_filter_begin", "hook_DrawPrimitive", "hook_DrawIndexedPrimitive"))
    with tempfile.TemporaryDirectory(prefix="prm-filter-test-") as directory:
        harness = Path(directory) / "filter.c"
        binary = Path(directory) / "filter-test"
        harness.write_text(PREFIX + types + STUBS + production + TESTS)
        compiler = shlex.split(os.environ.get("CC", "clang"))
        subprocess.run(compiler + ["-std=c11", "-O1", "-g", "-Wall", "-Wextra", "-Werror",
                                   "-fsanitize=address,undefined", "-fno-sanitize-recover=all",
                                   "-fno-omit-frame-pointer", str(harness), "-o", str(binary)], check=True)
        subprocess.run([str(binary)], check=True)
    print("PASS: actual filter scopes and DP/DIP hooks; scaler boundary and COM device are native stubs")


if __name__ == "__main__":
    main()
