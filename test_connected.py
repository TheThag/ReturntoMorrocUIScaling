#!/usr/bin/env python3
"""Exercise the production BasicInfo/Menu connected-window fit.

The harness extracts ``owner_fit_rect``, ``owner_fit_connected``, the active
manager-list walk, and the bitmap preparation gate from ``prm_uifix.c``.  The
native objects, vtable pointers, IDs, parent fields, and manager list are real
32-bit fixture memory, so the connected path is tested with the same pointer
width and sanitizer instrumentation as the game ABI.
"""

from pathlib import Path
import os
import re
import shlex
import subprocess
import sys
import tempfile


sys.dont_write_bytecode = True


def extract_type(source, name):
    match = re.search(
        r"typedef\s+struct\s*\{[^}]*\}\s*" + re.escape(name) + r"\s*;",
        source,
        re.S,
    )
    if not match:
        raise ValueError(f"missing production type {name}")
    return match[0]


def extract_function(source, name):
    """Extract a definition, skipping a same-named forward declaration."""
    candidates = re.finditer(
        r"^static [^\n]*\b" + re.escape(name) + r"\s*\(", source, re.M
    )
    for start in candidates:
        opening = source.find("{", start.start())
        if opening < 0:
            continue
        if source.find(";", start.start(), opening) >= 0:
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


PREFIX = r'''
#include <assert.h>
#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
typedef int32_t LONG;
typedef uint32_t DWORD;
typedef uint8_t BYTE;
/* The production source casts object addresses through ULONG_PTR. */
typedef uint32_t ULONG_PTR;
typedef struct { float l,t,r,b; } UIRectF;
typedef DWORD (*PFN_GetCurrentThreadId)(void);

static int failures;
#define CHECK(expression) do { \
    if (!(expression)) { \
        fprintf(stderr, "FAIL line %d: %s\n", __LINE__, #expression); \
        ++failures; \
    } \
} while (0)
'''


STUBS = r'''
#define MAX_OWNER_WINDOWS 512
#define FAKE_EXE_SIZE (0xAB76D8UL + 0x500UL)
#define MANAGER_RVA 0xAB76D8UL

static void owner_popup_trace_first(OwnerWindowState* st) { (void)st; }
static int owner_is_buff_tooltip(DWORD obj) { (void)obj; return 0; }
static void owner_buff_popup_offset(OwnerWindowState* st,LONG x,LONG y,LONG w) { (void)st; (void)x; (void)y; (void)w; }
static DWORD g_ui_present_serial;
static int g_owner_scale_enabled;
static int g_owner_submit_enabled;
static int g_owner_tooltip_enabled;
static int g_owner_bitmap_hooks_installed;
static int g_ui_runtime_enabled;
static int g_ui_keep_on_screen;
static int g_ui_scale_global;
static int g_ui_anchor_mode;
static int g_ui_global_threshold_percent;
static int g_ui_scale_percent;
static LONG g_ui_screen_w,g_ui_screen_h,g_ui_origin_x,g_ui_origin_y;
static DWORD g_owner_input_order;
static DWORD g_owner_bitmap_frame_calls,g_owner_bitmap_order;
static DWORD g_owner_bitmap_unsupported;
static OwnerBitmapScope g_owner_bitmap_scope;
static PFN_GetCurrentThreadId g_GetCurrentThreadId;

/* Current pair snapshot variables are declared beside the production helper. */
static DWORD g_owner_fit_pair_tag,g_owner_fit_pair_basic,g_owner_fit_pair_menu;
static DWORD g_owner_fit_pair_basic_vt,g_owner_fit_pair_menu_vt;
static float g_owner_fit_pair_ax,g_owner_fit_pair_ay,g_owner_fit_pair_scale;
static float g_owner_fit_pair_dx,g_owner_fit_pair_dy;
static int owner_bitmap_prepare(DWORD,LONG,LONG,LONG,LONG);

/* The connected-window fixture has no published mouse-region source. */
static void owner_popup_offset(OwnerWindowState* st,LONG x,LONG y,float* dx,float* dy) {
    (void)st; (void)x; (void)y; (void)dx; (void)dy;
}
/* The connected-window fixture has no native tooltip controller. */
static int owner_is_transient_tooltip(DWORD obj) { return obj==1; }

enum {
    BASIC = 0,
    MENU = 1,
    OTHER = 2,
    NATIVE_COUNT = 3,
    VT_BASIC = 0,
    VT_MENU = 1,
    VT_OTHER = 2,
    VT_REUSED = 3,
    VT_COUNT = 4
};

/* The manager and list nodes live in the fake module image. The UIWindow
 * objects and vtables live in separate native-looking fixture allocations. */
static BYTE g_fake_exe[FAKE_EXE_SIZE];
static BYTE g_native[NATIVE_COUNT][0x80];
static BYTE g_vtables[VT_COUNT][0x40];
static BYTE *g_exe;
static DWORD g_exe_size;
static OwnerWindowState g_owner_windows[NATIVE_COUNT];
static DWORD g_owner_window_count;

static int range_readable(const void *p,DWORD bytes,const void *base,size_t size) {
    uintptr_t q=(uintptr_t)p,b=(uintptr_t)base;
    if(!p || !bytes || q<b || q>b+size) return 0;
    return (uintptr_t)bytes <= b+size-q;
}
static int mem_readable(const void *p,DWORD bytes) {
    return range_readable(p,bytes,g_fake_exe,sizeof(g_fake_exe)) ||
           range_readable(p,bytes,g_native,sizeof(g_native)) ||
           range_readable(p,bytes,g_vtables,sizeof(g_vtables));
}
static float ui_scale_factor(void) {
    return ((float)g_ui_scale_percent)*0.01f;
}
static DWORD current_thread(void) { return 17; }

/* Existing states are copied records. On a normal lookup the live first word
 * must still equal the copied vtable pointer; a reused address therefore
 * cannot silently resurrect an old owner through this fixture boundary. */
static OwnerWindowState* owner_state_for(DWORD object,int create) {
    DWORD i;
    (void)create;
    for(i=0;i<g_owner_window_count;++i) {
        OwnerWindowState *st=&g_owner_windows[i];
        if(st->object_ptr!=object) continue;
        if(mem_readable((void*)(ULONG_PTR)object,4) &&
           *(DWORD*)(ULONG_PTR)object==st->vtable_ptr) return st;
        return 0;
    }
    return 0;
}

static void put32(void *base,DWORD offset,DWORD value) {
    memcpy((BYTE*)base+offset,&value,sizeof(value));
}
static DWORD get32(const void *base,DWORD offset) {
    DWORD value;
    memcpy(&value,(const BYTE*)base+offset,sizeof(value));
    return value;
}
static DWORD native_ptr(int index) {
    return (DWORD)(ULONG_PTR)&g_native[index][0];
}
static DWORD native_vt(int index) {
    return (DWORD)(ULONG_PTR)&g_vtables[index][0];
}
static void native_vtable(int index,int vt_index) {
    put32(g_native[index],0,native_vt(vt_index));
}
static void native_window(int index,int vt_index,DWORD id,LONG x,LONG y,
                          LONG w,LONG h) {
    memset(g_native[index],0,sizeof(g_native[index]));
    native_vtable(index,vt_index);
    put32(g_native[index],0x14,(DWORD)w);
    put32(g_native[index],0x18,(DWORD)h);
    put32(g_native[index],0x1c,(DWORD)x);
    put32(g_native[index],0x20,(DWORD)y);
    put32(g_native[index],0x28,1);
    put32(g_native[index],0x2c,id);
}
static void native_parent(int index,DWORD parent) {
    put32(g_native[index],0x10,parent);
}
static void owner_state(int index,const char *class_name,int vt_index) {
    OwnerWindowState *st=&g_owner_windows[index];
    memset(st,0,sizeof(*st));
    st->object_ptr=native_ptr(index);
    st->vtable_ptr=native_vt(vt_index);
    strcpy(st->class_name,class_name);
}
static void manager_list(int reverse,int include_basic,int include_menu,
                         int include_other) {
    BYTE *mgr=g_exe+MANAGER_RVA;
    BYTE *head=g_exe+MANAGER_RVA+0x300;
    BYTE *nodes[3]={g_exe+MANAGER_RVA+0x320,
                   g_exe+MANAGER_RVA+0x340,
                   g_exe+MANAGER_RVA+0x360};
    int order[3],count=0,i;
    memset(g_exe+MANAGER_RVA+0x174,0,0x20);
    memset(head,0,0x80);
    for(i=0;i<3;++i) memset(nodes[i],0,0x20);
    if(reverse) {
        if(include_menu) order[count++]=MENU;
        if(include_basic) order[count++]=BASIC;
    } else {
        if(include_basic) order[count++]=BASIC;
        if(include_menu) order[count++]=MENU;
    }
    if(include_other) order[count++]=OTHER;
    put32(head,0,count ? (DWORD)(ULONG_PTR)nodes[0] :
          (DWORD)(ULONG_PTR)head);
    for(i=0;i<count;++i) {
        BYTE *node=nodes[i];
        put32(node,0,(DWORD)(ULONG_PTR)(i+1<count ? nodes[i+1] : head));
        put32(node,8,native_ptr(order[i]));
    }
    put32(mgr,0x174,(DWORD)(ULONG_PTR)head);
}
static LONG native_long(int index,DWORD offset) {
    return (LONG)get32(g_native[index],offset);
}

static void fixture_reset(int percent) {
    memset(g_fake_exe,0,sizeof(g_fake_exe));
    memset(g_native,0,sizeof(g_native));
    memset(g_vtables,0,sizeof(g_vtables));
    memset(g_owner_windows,0,sizeof(g_owner_windows));
    memset(&g_owner_bitmap_scope,0,sizeof(g_owner_bitmap_scope));
    g_exe=g_fake_exe; g_exe_size=sizeof(g_fake_exe);
    g_ui_present_serial=100;
    g_owner_scale_enabled=g_owner_submit_enabled=g_owner_tooltip_enabled=1;
    g_owner_bitmap_hooks_installed=1; g_ui_runtime_enabled=1;
    g_ui_keep_on_screen=1; g_ui_scale_global=0;
    g_ui_anchor_mode=1; g_ui_global_threshold_percent=75;
    g_ui_scale_percent=percent;
    g_ui_screen_w=1920; g_ui_screen_h=1080;
    g_ui_origin_x=g_ui_origin_y=0;
    g_owner_input_order=0; g_owner_bitmap_frame_calls=0;
    g_owner_bitmap_order=0; g_owner_bitmap_unsupported=0;
    g_owner_window_count=NATIVE_COUNT;
    g_owner_fit_pair_tag=0; g_owner_fit_pair_basic=0; g_owner_fit_pair_menu=0;
    g_owner_fit_pair_basic_vt=0; g_owner_fit_pair_menu_vt=0;
    g_owner_fit_pair_ax=g_owner_fit_pair_ay=g_owner_fit_pair_scale=0.0f;
    g_owner_fit_pair_dx=g_owner_fit_pair_dy=0.0f;
    g_GetCurrentThreadId=current_thread;

    /* A Basic root and the separately registered icon menu overlap by four
       native pixels, and their union runs below the 200% desktop edge. */
    native_window(BASIC,VT_BASIC,0,1400,840,220,134);
    native_window(MENU,VT_MENU,0x133,1400,970,220,197);
    native_window(OTHER,VT_OTHER,0x2a,600,200,180,100);
    owner_state(BASIC,"UIBasicInfoWnd",VT_BASIC);
    owner_state(MENU,"UIMenuIconWnd",VT_MENU);
    owner_state(OTHER,"UIOtherWnd",VT_OTHER);
    manager_list(0,1,1,0);
}

static void native_rect(int index,UIRectF *out) {
    LONG x=native_long(index,0x1c),y=native_long(index,0x20);
    LONG w=native_long(index,0x14),h=native_long(index,0x18);
    out->l=(float)x; out->t=(float)y;
    out->r=(float)(x+w); out->b=(float)(y+h);
}
static void fitted_rect(int index,const OwnerWindowState *st,UIRectF *out) {
    UIRectF in; float scale=st->fit_scale;
    native_rect(index,&in);
    out->l=st->ax+(in.l-st->ax)*scale+st->offset_x;
    out->r=st->ax+(in.r-st->ax)*scale+st->offset_x;
    out->t=st->ay+(in.t-st->ay)*scale+st->offset_y;
    out->b=st->ay+(in.b-st->ay)*scale+st->offset_y;
}
static void union_rect(UIRectF *a,const UIRectF *b) {
    if(b->l<a->l) a->l=b->l; if(b->t<a->t) a->t=b->t;
    if(b->r>a->r) a->r=b->r; if(b->b>a->b) a->b=b->b;
}
static void assert_pair_bounds(void) {
    UIRectF a,b,all;
    native_rect(BASIC,&a); native_rect(MENU,&b); union_rect(&a,&b); all=a;
    fitted_rect(BASIC,&g_owner_windows[BASIC],&a);
    fitted_rect(MENU,&g_owner_windows[MENU],&b);
    union_rect(&a,&b);
    CHECK(a.l>=-0.01f && a.t>=-0.01f);
    CHECK(a.r<=g_ui_screen_w+0.01f && a.b<=g_ui_screen_h+0.01f);
    CHECK(all.r-all.l>0.0f && all.b-all.t>0.0f);
}
static void assert_pair_transform(void) {
    OwnerWindowState *basic=&g_owner_windows[BASIC];
    OwnerWindowState *menu=&g_owner_windows[MENU];
    CHECK(fabsf(basic->fit_scale-menu->fit_scale)<0.001f);
    CHECK(fabsf(basic->ax-menu->ax)<0.001f);
    CHECK(fabsf(basic->ay-menu->ay)<0.001f);
    CHECK(fabsf(basic->offset_x-menu->offset_x)<0.001f);
    CHECK(fabsf(basic->offset_y-menu->offset_y)<0.001f);
    CHECK(fabsf(basic->fit_scale-2.0f)<0.001f);
    CHECK(fabsf(basic->offset_x)<0.001f);
    CHECK(fabsf(basic->offset_y+174.0f)<0.01f);
    CHECK(fabsf(basic->ax-1920.0f)<0.001f);
    CHECK(fabsf(basic->ay-1080.0f)<0.001f);
    assert_pair_bounds();
}
static void prepare_native(int index) {
    CHECK(owner_bitmap_prepare(native_ptr(index),native_long(index,0x1c),
                               native_long(index,0x20),native_long(index,0x14),
                               native_long(index,0x18)));
}
'''


FUNCTIONS = (
    "s_len",
    "s_contains",
    "s_equal",
    "owner_class_is_hover_popup",
    "owner_class_is_world_label",
    "owner_class_is_world_title",
    "owner_class_is_world_name",
    "rect_is_global",
    "choose_group_anchor",
    "rect_union",
    "owner_input_touch_state",
    "owner_fit_rect",
    "owner_collect_active_objects",
    "owner_fit_connected",
    "owner_bitmap_prepare",
)


TESTS = r'''
static void test_fit_rect_direct(void) {
    UIRectF whole={1400.0f,840.0f,1620.0f,1167.0f};
    float scale=2.0f,dx=0.0f,dy=0.0f;
    fixture_reset(200);
    owner_fit_rect(&whole,1920.0f,1080.0f,&scale,&dx,&dy);
    CHECK(fabsf(scale-2.0f)<0.001f);
    CHECK(fabsf(dx)<0.001f && fabsf(dy+174.0f)<0.01f);
    CHECK(fabsf(1080.0f+(whole.b-1080.0f)*scale+dy-1080.0f)<0.01f);
    puts("PASS fit helper: whole connected bounds clamp at the 200% bottom edge");
}

static void test_draw_orders(void) {
    int reverse;
    for(reverse=0;reverse<2;++reverse) {
        OwnerWindowState *first,*second;
        fixture_reset(200);
        manager_list(reverse,1,1,0);
        first=&g_owner_windows[reverse?MENU:BASIC];
        second=&g_owner_windows[reverse?BASIC:MENU];
        CHECK(owner_fit_connected(first));
        CHECK(owner_fit_connected(second));
        assert_pair_transform();
        /* Exercise the same preparation boundary in each native draw order. */
        prepare_native(reverse?MENU:BASIC);
        prepare_native(reverse?BASIC:MENU);
        CHECK(g_owner_bitmap_frame_calls==2);
        CHECK(g_owner_bitmap_scope.object_ptr==native_ptr(reverse?BASIC:MENU));
        CHECK(fabsf(g_owner_bitmap_scope.fit_scale-2.0f)<0.001f);
        CHECK(fabsf(g_owner_bitmap_scope.offset_y+174.0f)<0.01f);
    }
    puts("PASS connected pair: BasicInfo/Menu native roots share one fit in both manager/draw orders");
}

static void test_supported_scales(void) {
    const int percentages[]={125,133,150,175,200};
    unsigned int i;
    for(i=0;i<sizeof(percentages)/sizeof(percentages[0]);++i) {
        UIRectF basic,menu,all;
        fixture_reset(percentages[i]);
        CHECK(owner_fit_connected(&g_owner_windows[BASIC]));
        CHECK(owner_fit_connected(&g_owner_windows[MENU]));
        fitted_rect(BASIC,&g_owner_windows[BASIC],&basic);
        fitted_rect(MENU,&g_owner_windows[MENU],&menu);
        all=basic; union_rect(&all,&menu);
        CHECK(all.l>=-0.01f && all.t>=-0.01f);
        CHECK(all.r<=g_ui_screen_w+0.01f && all.b<=g_ui_screen_h+0.01f);
        CHECK(fabsf((menu.t-basic.b)-
                    ((970.0f-(840.0f+134.0f))*g_owner_windows[BASIC].fit_scale))<0.01f);
    }
    puts("PASS connected scales: 125/133/150/175/200% preserve pair spacing and screen bounds");
}

static void test_next_frame_move(void) {
    float old_dx,old_dy,old_scale;
    float old_gap,new_gap;
    UIRectF basic,menu;
    fixture_reset(200);
    CHECK(owner_fit_connected(&g_owner_windows[BASIC]));
    CHECK(owner_fit_connected(&g_owner_windows[MENU]));
    old_dx=g_owner_windows[BASIC].offset_x;
    old_dy=g_owner_windows[BASIC].offset_y;
    old_scale=g_owner_windows[BASIC].fit_scale;
    fitted_rect(BASIC,&g_owner_windows[BASIC],&basic);
    fitted_rect(MENU,&g_owner_windows[MENU],&menu);
    old_gap=menu.t-basic.b;

    /* Move the native pair together through the next present. The retained
       edge correction belongs to the connected block, while spacing follows
       the new native coordinates at the same fit scale. */
    put32(g_native[BASIC],0x1c,(DWORD)(native_long(BASIC,0x1c)+50));
    put32(g_native[BASIC],0x20,(DWORD)(native_long(BASIC,0x20)-40));
    put32(g_native[MENU],0x1c,(DWORD)(native_long(MENU,0x1c)+50));
    put32(g_native[MENU],0x20,(DWORD)(native_long(MENU,0x20)-40));
    ++g_ui_present_serial;
    CHECK(owner_fit_connected(&g_owner_windows[BASIC]));
    CHECK(owner_fit_connected(&g_owner_windows[MENU]));
    fitted_rect(BASIC,&g_owner_windows[BASIC],&basic);
    fitted_rect(MENU,&g_owner_windows[MENU],&menu);
    new_gap=menu.t-basic.b;
    CHECK(fabsf(g_owner_windows[BASIC].offset_x-old_dx)<0.001f);
    CHECK(fabsf(g_owner_windows[BASIC].offset_y-old_dy)<0.001f);
    CHECK(fabsf(g_owner_windows[BASIC].fit_scale-old_scale)<0.001f);
    CHECK(fabsf(new_gap-old_gap)<0.01f);
    assert_pair_bounds();
    puts("PASS connected lifetime: next-frame movement retains the correction and pair spacing");
}

static void test_missing_owner(void) {
    fixture_reset(200);
    manager_list(0,1,0,0);
    CHECK(!owner_fit_connected(&g_owner_windows[BASIC]));
    CHECK(!g_owner_fit_pair_basic && !g_owner_fit_pair_menu);
    prepare_native(BASIC);
    CHECK(fabsf(g_owner_windows[BASIC].offset_y)<0.001f);

    fixture_reset(200);
    manager_list(0,0,1,0);
    CHECK(!owner_fit_connected(&g_owner_windows[MENU]));
    CHECK(!g_owner_fit_pair_basic && !g_owner_fit_pair_menu);
    puts("PASS missing owner: an absent Basic or Menu root passes through without borrowing a pair fit");
}

static void test_disabled_gates(void) {
    int *gates[]={&g_owner_scale_enabled,&g_owner_submit_enabled,
                  &g_owner_bitmap_hooks_installed};
    unsigned int i;
    for(i=0;i<sizeof(gates)/sizeof(gates[0]);++i) {
        fixture_reset(200);
        g_owner_bitmap_scope.object_ptr=0x12345678UL;
        g_owner_bitmap_scope.thread=77;
        *gates[i]=0;
        CHECK(!owner_bitmap_prepare(native_ptr(BASIC),1400,840,220,134));
        CHECK(!g_owner_bitmap_scope.object_ptr && !g_owner_bitmap_scope.thread);
        CHECK(g_owner_bitmap_frame_calls==0);
    }
    puts("PASS disabled gates: scale, submit, and hook gates clear scope and bypass connected fitting");
}

static void test_vtable_reuse(void) {
    fixture_reset(200);
    CHECK(owner_fit_connected(&g_owner_windows[BASIC]));
    CHECK(owner_fit_connected(&g_owner_windows[MENU]));
    /* Keep the copied state and pair tag, but reuse the native address with a
       different vtable. Both cached pair members must reject this snapshot. */
    native_vtable(BASIC,VT_REUSED);
    CHECK(!owner_fit_connected(&g_owner_windows[BASIC]));
    CHECK(!owner_fit_connected(&g_owner_windows[MENU]));
    CHECK(!owner_bitmap_prepare(native_ptr(BASIC),1400,840,220,134));
    CHECK(!g_owner_bitmap_scope.object_ptr && !g_owner_bitmap_scope.thread);
    ++g_ui_present_serial;
    CHECK(!owner_fit_connected(&g_owner_windows[MENU]));
    puts("PASS vtable identity: reused native addresses cannot borrow a cached connected fit");
}

static void test_parent_and_unrelated(void) {
    fixture_reset(200);
    native_parent(BASIC,native_ptr(OTHER));
    CHECK(!owner_fit_connected(&g_owner_windows[BASIC]));
    CHECK(!owner_fit_connected(&g_owner_windows[MENU]));
    CHECK(!g_owner_fit_pair_basic && !g_owner_fit_pair_menu);

    fixture_reset(200);
    strcpy(g_owner_windows[BASIC].class_name,"UIOtherWnd");
    CHECK(!owner_fit_connected(&g_owner_windows[BASIC]));
    CHECK(!owner_fit_connected(&g_owner_windows[MENU]));
    CHECK(!g_owner_fit_pair_basic && !g_owner_fit_pair_menu);

    fixture_reset(200);
    native_window(MENU,VT_MENU,0x999,1400,970,220,197);
    CHECK(!owner_fit_connected(&g_owner_windows[BASIC]));
    CHECK(!g_owner_fit_pair_basic && !g_owner_fit_pair_menu);
    puts("PASS admission: parented roots, unrelated classes, and wrong native IDs are never grouped");
}

int main(void) {
    CHECK(sizeof(void*)==4 && sizeof(ULONG_PTR)==4);
    test_fit_rect_direct();
    test_draw_orders();
    test_supported_scales();
    test_next_frame_move();
    test_missing_owner();
    test_disabled_gates();
    test_vtable_reuse();
    test_parent_and_unrelated();
    if(failures) {
        fprintf(stderr,"connected-window harness: %d assertion(s) failed\n",failures);
        return 1;
    }
    puts("PASS connected-window harness: extracted 32-bit ASan/UBSan production fit and active-list path");
    return 0;
}
'''


def main():
    source_path = Path(__file__).resolve().with_name("prm_uifix.c")
    source = source_path.read_text()
    types = "\n".join(extract_type(source, name) for name in (
        "OwnerWindowState", "OwnerBitmapScope"))
    functions = "\n".join(extract_function(source, name) for name in FUNCTIONS)
    code = PREFIX + types + STUBS + functions + TESTS
    with tempfile.TemporaryDirectory(prefix="prm-connected-test-") as directory:
        c_file = Path(directory) / "connected.c"
        binary = Path(directory) / "connected-test"
        c_file.write_text(code)
        compiler = shlex.split(os.environ.get("CC", "clang"))
        subprocess.run(
            compiler + [
                "-m32", "-std=c11", "-O1", "-g", "-Wall", "-Wextra",
                "-Wno-unused-variable", "-Wno-unused-parameter",
                "-Wno-unused-function", "-fsanitize=address,undefined",
                "-fno-sanitize-recover=all", "-fno-omit-frame-pointer",
                str(c_file), "-o", str(binary),
            ],
            check=True,
        )
        subprocess.run([str(binary)], check=True)


if __name__ == "__main__":
    main()
