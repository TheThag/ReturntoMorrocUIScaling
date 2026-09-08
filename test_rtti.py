#!/usr/bin/env python3
"""Exercise production RTTI validation and generic UIWindow admission.

The fixture builds bounded MSVC x86 RTTI metadata in a synthetic executable
image.  Leaf names are deliberately anonymous for the UIWindow-family cases,
so admission is proved by the native base hierarchy and PMD values rather than
by a dialog-name exception.  It also exercises the real owner_state_for()
boundary and malformed/truncated metadata paths under 32-bit ASan/UBSan.
"""

import os
from pathlib import Path
import re
import shlex
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True


ROOT = Path(__file__).resolve().parent
SOURCE = (ROOT / "prm_uifix.c").read_text()


def extract_type(source, name):
    marker = "} " + name + ";"
    end = source.find(marker)
    if end < 0:
        raise RuntimeError(f"missing production type {name}")
    start = source.rfind("typedef struct {", 0, end)
    if start < 0:
        raise RuntimeError(f"missing typedef for {name}")
    return source[start:end + len(marker)]


def extract_function(source, name):
    start = re.search(
        r"^static [^\n]*\b" + re.escape(name) + r"\s*\([^;]*?\)\s*\{",
        source,
        re.M,
    )
    if not start:
        raise RuntimeError(f"missing production function {name}")
    opening = source.find("{", start.start())
    depth = 0
    for token in re.finditer(
        r"/\*.*?\*/|//[^\n]*|\"(?:\\.|[^\"\\])*\"|"
        r"'(?:\\.|[^'\\])*'|[{}]",
        source[opening:],
        re.S,
    ):
        if token[0] == "{":
            depth += 1
        elif token[0] == "}":
            depth -= 1
            if depth == 0:
                return source[start.start():opening + token.end()]
    raise RuntimeError(f"unterminated production function {name}")


PREFIX = r'''
#include <assert.h>
#include <stdint.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef uint8_t BYTE;
typedef uint16_t WORD;
typedef uint32_t DWORD;
typedef int32_t LONG;
typedef uintptr_t ULONG_PTR;
typedef void *HMODULE;
typedef struct { float l,t,r,b; } UIRectF;
typedef struct { LONG x,y; } POINT;

#define MAX_OWNER_WINDOWS 64
#define CHECK(x) do { if (!(x)) { \
    fprintf(stderr, "check failed at line %d: %s\n", __LINE__, #x); \
    exit(1); \
} } while (0)

static HMODULE g_exe;
static DWORD g_exe_size;
static DWORD g_ui_present_serial;
static int g_ui_scale_percent;

static void s_copy(char *dst, unsigned int cap, const char *src) {
    unsigned int i=0;
    if (!dst || !cap) return;
    while (src && src[i] && i+1<cap) { dst[i]=src[i]; ++i; }
    dst[i]=0;
}
'''


STUBS = r'''
/* The production code asks VirtualQuery-backed mem_readable() before every
   native dereference.  These explicit ranges provide the same fail-closed
   boundary for the synthetic 32-bit image and objects. */
typedef struct { uintptr_t base; size_t size; } ReadRange;
#define MAX_READ_RANGES 4
static ReadRange g_read_ranges[MAX_READ_RANGES];
static unsigned int g_read_range_count;

static int range_readable(const void *p, DWORD bytes,
                          const void *base, size_t size) {
    uintptr_t q=(uintptr_t)p, b=(uintptr_t)base;
    if (!p || !bytes || q < b) return 0;
    if (q-b > size) return 0;
    return (uintptr_t)bytes <= size-(q-b);
}

static int mem_readable(const void *p, DWORD bytes) {
    unsigned int i;
    if (!p || !bytes) return 0;
    for (i=0; i<g_read_range_count; ++i) {
        uintptr_t b=g_read_ranges[i].base;
        uintptr_t q=(uintptr_t)p;
        if (q >= b && q-b <= g_read_ranges[i].size &&
            (uintptr_t)bytes <= g_read_ranges[i].size-(q-b)) return 1;
    }
    return 0;
}

static void owner_input_region_lock(void) {}
static void owner_input_region_unlock(void) {}
static OwnerWindowState *owner_state_reclaim_slot(void) { return 0; }

static OwnerWindowState g_owner_windows[MAX_OWNER_WINDOWS];
static DWORD g_owner_window_count;
static DWORD g_owner_window_reclaimed;
static DWORD g_owner_window_reclaim_blocked;

static OwnerInputRegion g_owner_input_regions[8];
static DWORD g_owner_input_region_count;
'''


TESTS = r'''
#define IMAGE_BYTES 0x20000U
#define MAX_OBJECTS 64

typedef struct { DWORD vtable; BYTE padding[28]; } FakeObject;
typedef struct {
    DWORD object, vtable, col, leaf_td, chd, array;
    DWORD window_bcd, balloon_bcd;
} RttiCase;

static BYTE image[IMAGE_BYTES];
static FakeObject objects[MAX_OBJECTS];
static RttiCase cases[MAX_OBJECTS];
static size_t image_cursor;

static DWORD ptr32(const void *p) {
    uintptr_t value=(uintptr_t)p;
    CHECK(value<=UINT32_MAX);
    return (DWORD)value;
}

static DWORD image_ptr(size_t offset) {
    CHECK(offset < IMAGE_BYTES);
    return ptr32(image+offset);
}

static size_t image_offset(DWORD address) {
    DWORD base=ptr32(image);
    CHECK(address>=base && (size_t)(address-base)<IMAGE_BYTES);
    return (size_t)(address-base);
}

static void write_word(DWORD address, DWORD value) {
    size_t offset=image_offset(address);
    CHECK(offset+sizeof(value)<=IMAGE_BYTES);
    memcpy(image+offset,&value,sizeof(value));
}

static DWORD read_word(DWORD address) {
    DWORD value;
    size_t offset=image_offset(address);
    CHECK(offset+sizeof(value)<=IMAGE_BYTES);
    memcpy(&value,image+offset,sizeof(value));
    return value;
}

static size_t image_alloc(size_t bytes) {
    size_t offset=(image_cursor+3U)&~(size_t)3U;
    CHECK(offset<=IMAGE_BYTES && bytes<=IMAGE_BYTES-offset);
    memset(image+offset,0,bytes);
    image_cursor=offset+bytes;
    return offset;
}

static DWORD image_td(const char *leaf) {
    size_t offset=image_alloc(256);
    BYTE *raw=image+offset+8;
    size_t n=strlen(leaf);
    CHECK(n<160);
    raw[0]='.'; raw[1]='?'; raw[2]='A'; raw[3]='V';
    memcpy(raw+4,leaf,n);
    raw[4+n]='@'; raw[5+n]='@'; raw[6+n]=0;
    return image_ptr(offset);
}

static DWORD image_base_td(const char *base_name) {
    CHECK(strlen(base_name)<160);
    return image_td(base_name);
}

static DWORD image_bcd(DWORD td, LONG mdisp, LONG pdisp, LONG vdisp) {
    size_t offset=image_alloc(32);
    write_word(image_ptr(offset),td);
    write_word(image_ptr(offset+4),1);
    write_word(image_ptr(offset+8),(DWORD)mdisp);
    write_word(image_ptr(offset+12),(DWORD)pdisp);
    write_word(image_ptr(offset+16),(DWORD)vdisp);
    return image_ptr(offset);
}

static void clear_fixture(void) {
    memset(image,0,sizeof(image));
    memset(objects,0,sizeof(objects));
    memset(cases,0,sizeof(cases));
    image_cursor=0x100;
    g_exe=(HMODULE)image;
    g_exe_size=IMAGE_BYTES;
    g_read_range_count=2;
    g_read_ranges[0]=(ReadRange){(uintptr_t)image,sizeof(image)};
    g_read_ranges[1]=(ReadRange){(uintptr_t)objects,sizeof(objects)};
    memset(g_owner_windows,0,sizeof(g_owner_windows));
    g_owner_window_count=0;
    g_owner_window_reclaimed=0;
    g_owner_window_reclaim_blocked=0;
}

/* ``base_kind`` 1 is a primary nonvirtual UIFrameWnd -> UIWindow hierarchy.
   Kind 2 adds UIBalloonText and is the separate balloon family. Kind 3 is a
   direct UIWindow descendant without the required UIFrameWnd base. */
static RttiCase build_case(unsigned int index, const char *leaf, int base_kind) {
    RttiCase c={0};
    DWORD descriptors[8];
    DWORD tds[8];
    unsigned int count=0,i;
    size_t col_off,chd_off,array_off,vt_slot;

    CHECK(index<MAX_OBJECTS);
    memset(&objects[index],0,sizeof(objects[index]));
    c.object=ptr32(&objects[index]);
    c.leaf_td=image_td(leaf);
    tds[count]=c.leaf_td;
    descriptors[count]=image_bcd(tds[count],0,-1,0);
    ++count;
    if (base_kind==1) {
        tds[count]=image_base_td("UIFrameWnd");
        descriptors[count]=image_bcd(tds[count],0,-1,0); ++count;
        tds[count]=image_base_td("UIWindow");
        descriptors[count]=image_bcd(tds[count],0,-1,0);
        c.window_bcd=descriptors[count]; ++count;
        tds[count]=image_base_td("UIRPData");
        descriptors[count]=image_bcd(tds[count],0,-1,0); ++count;
    } else if (base_kind==2) {
        tds[count]=image_base_td("UIBalloonText");
        descriptors[count]=image_bcd(tds[count],0,-1,0);
        c.balloon_bcd=descriptors[count]; ++count;
        tds[count]=image_base_td("UIWindow");
        descriptors[count]=image_bcd(tds[count],0,-1,0);
        c.window_bcd=descriptors[count]; ++count;
    } else if (base_kind==3) {
        tds[count]=image_base_td("UIWindow");
        descriptors[count]=image_bcd(tds[count],0,-1,0);
        c.window_bcd=descriptors[count]; ++count;
    }

    array_off=image_alloc(count*4);
    for (i=0; i<count; ++i) write_word(image_ptr(array_off+i*4),descriptors[i]);
    chd_off=image_alloc(16);
    write_word(image_ptr(chd_off),0);              /* CHD signature. */
    write_word(image_ptr(chd_off+4),0);            /* attributes. */
    write_word(image_ptr(chd_off+8),count);
    write_word(image_ptr(chd_off+12),image_ptr(array_off));
    col_off=image_alloc(20);
    write_word(image_ptr(col_off),0);              /* COL signature. */
    write_word(image_ptr(col_off+4),0);            /* object offset. */
    write_word(image_ptr(col_off+8),0);            /* cdOffset. */
    write_word(image_ptr(col_off+12),c.leaf_td);
    write_word(image_ptr(col_off+16),image_ptr(chd_off));
    vt_slot=image_alloc(32)+4;                    /* leave vtable[-1]. */
    write_word(image_ptr(vt_slot-4),image_ptr(col_off));
    c.vtable=image_ptr(vt_slot);
    objects[index].vtable=c.vtable;
    c.col=image_ptr(col_off);
    c.chd=image_ptr(chd_off);
    c.array=image_ptr(array_off);
    cases[index]=c;
    return c;
}

static void restore_name_bytes(DWORD td, BYTE *saved, size_t count) {
    memcpy((BYTE*)(ULONG_PTR)td+8,saved,count);
}

static void expect_name(const RttiCase *c, const char *expected) {
    char out[80];
    DWORD vr=0;
    memset(out,0,sizeof(out));
    CHECK(rtti_name_from_object(c->object,out,sizeof(out),&vr));
    CHECK(!strcmp(out,expected));
    CHECK(vr==c->vtable-ptr32(image));
}

static void test_anonymous_message_families(void) {
    static const char *names[]={
        "UIMessageBox", "UIMessageBoxOKCancel", "UIMessageBoxYesNo",
        "UIMessageBoxRetryIgnore"
    };
    unsigned int i;
    clear_fixture();
    for (i=0; i<sizeof(names)/sizeof(names[0]); ++i) {
        RttiCase c=build_case(i,names[i],1);
        OwnerWindowState *st;
        expect_name(&c,names[i]);
        CHECK(owner_rtti_window_family(c.object)==1);
        CHECK(!owner_class_should_hook(names[i]));
        CHECK(owner_object_should_hook(c.object,names[i]));
        st=owner_state_for(c.object,1);
        CHECK(st && st->object_ptr==c.object);
        CHECK(st->vtable_ptr==c.vtable);
        CHECK(!strcmp(st->class_name,names[i]));
    }
    /* A class-free leaf proves the hierarchy, rather than a UI prefix, is the
       admission reason. */
    {
        RttiCase c=build_case(10,"ConfirmActionLeaf",1);
        expect_name(&c,"ConfirmActionLeaf");
        CHECK(owner_rtti_window_family(c.object)==1);
        CHECK(!owner_class_should_hook("ConfirmActionLeaf"));
        CHECK(owner_object_should_hook(c.object,"ConfirmActionLeaf"));
        CHECK(owner_state_for(c.object,1)!=0);
    }
    CHECK(g_owner_window_count==5);
    puts("PASS: anonymous message-box variants and class-free UIFrameWnd -> UIWindow roots are admitted by RTTI hierarchy");
}

static void test_balloon_and_explicit_families(void) {
    const char *special[]={
        "UITransBalloonText", "UICharInfoBalloonText", "CSignBoardWnd",
        "UIPlayerGage", "UIChatRoomTitle", "UINameBalloonText",
        "UIVerticalNameBalloonText"
    };
    unsigned int i;
    clear_fixture();
    {
        RttiCase c=build_case(0,"AnonymousActorBalloon",2);
        expect_name(&c,"AnonymousActorBalloon");
        CHECK(owner_rtti_window_family(c.object)==2);
        CHECK(!owner_class_should_hook("AnonymousActorBalloon"));
        CHECK(!owner_object_should_hook(c.object,"AnonymousActorBalloon"));
        CHECK(!owner_state_for(c.object,1));
    }
    {
        RttiCase c=build_case(1,"UITransBalloonText",2);
        CHECK(owner_rtti_window_family(c.object)==2);
        CHECK(owner_class_should_hook("UITransBalloonText"));
        CHECK(owner_object_should_hook(c.object,"UITransBalloonText"));
        CHECK(owner_state_for(c.object,1)!=0);
    }
    {
        RttiCase c=build_case(2,"UIBalloonText",3);
        expect_name(&c,"UIBalloonText");
        CHECK(owner_rtti_window_family(c.object)==2);
        CHECK(!owner_class_should_hook("UIBalloonText"));
        CHECK(!owner_state_for(c.object,1));
    }
    for (i=0; i<sizeof(special)/sizeof(special[0]); ++i) {
        RttiCase c=build_case(8+i,special[i],0);
        expect_name(&c,special[i]);
        CHECK(owner_rtti_window_family(c.object)==0);
        CHECK(owner_class_should_hook(special[i]));
        CHECK(owner_object_should_hook(c.object,special[i]));
        CHECK(owner_state_for(c.object,1)!=0);
    }
    {
        static const char *excluded[]={
            "CBmpObjWnd", "UIPcGage", "UIMonsterGage", "UIMerchantShopTitle"
        };
        for (i=0; i<sizeof(excluded)/sizeof(excluded[0]); ++i) {
            RttiCase c=build_case(24+i,excluded[i],3);
            expect_name(&c,excluded[i]);
            CHECK(owner_rtti_window_family(c.object)==0);
            CHECK(!owner_object_should_hook(c.object,excluded[i]));
            CHECK(!owner_state_for(c.object,1));
        }
    }
    {
        RttiCase c=build_case(20,"UnrelatedLeaf",0);
        expect_name(&c,"UnrelatedLeaf");
        CHECK(owner_rtti_window_family(c.object)==0);
        CHECK(!owner_class_should_hook("UnrelatedLeaf"));
        CHECK(!owner_object_should_hook(c.object,"UnrelatedLeaf"));
        CHECK(!owner_state_for(c.object,1));
    }
    puts("PASS: balloon family stays rejected unless an explicit attachment class policy admits it; special roots remain supported");
}

static void test_image_bounds_and_invalid_objects(void) {
    RttiCase c;
    DWORD old;
    BYTE *raw;
    BYTE saved[160];
    char out[80];
    DWORD vr;

    clear_fixture();
    c=build_case(0,"MessageLeaf",1);
    CHECK(rtti_image_readable(image_ptr(0x100),4));
    CHECK(!rtti_image_readable(image_ptr(IMAGE_BYTES-2),4));
    CHECK(!rtti_image_readable(image_ptr(0x100),0));
    CHECK(!rtti_image_readable(ptr32(image)-1,4));
    CHECK(!rtti_image_readable(0xffffffffUL,4));
    CHECK(!rtti_name_from_object(0, out,sizeof(out),&vr));
    CHECK(!rtti_name_from_object(0x41414141UL,out,sizeof(out),&vr));
    CHECK(owner_rtti_window_family(0)==0);
    CHECK(owner_rtti_window_family(0x41414141UL)==0);

    old=objects[0].vtable; objects[0].vtable=0x41414141UL;
    CHECK(!rtti_name_from_object(c.object,out,sizeof(out),&vr));
    CHECK(owner_rtti_window_family(c.object)==0);
    objects[0].vtable=old;

    old=read_word(c.vtable-4); write_word(c.vtable-4,0x41414141UL);
    CHECK(!rtti_name_from_object(c.object,out,sizeof(out),&vr));
    CHECK(owner_rtti_window_family(c.object)==0);
    write_word(c.vtable-4,old);

    old=read_word(c.col); write_word(c.col,1);
    CHECK(rtti_name_from_object(c.object,out,sizeof(out),&vr));
    CHECK(owner_rtti_window_family(c.object)==0);
    write_word(c.col,old);

    old=read_word(c.chd); write_word(c.chd,1);
    CHECK(owner_rtti_window_family(c.object)==0);
    write_word(c.chd,old);

    old=read_word(c.chd+8); write_word(c.chd+8,0);
    CHECK(owner_rtti_window_family(c.object)==0);
    write_word(c.chd+8,old);
    old=read_word(c.chd+8); write_word(c.chd+8,65);
    CHECK(owner_rtti_window_family(c.object)==0);
    write_word(c.chd+8,old);

    old=read_word(c.chd+12); write_word(c.chd+12,0x41414141UL);
    CHECK(owner_rtti_window_family(c.object)==0);
    write_word(c.chd+12,old);

    old=read_word(c.array); write_word(c.array,0x41414141UL);
    CHECK(owner_rtti_window_family(c.object)==0);
    write_word(c.array,old);

    old=read_word(c.window_bcd+8); write_word(c.window_bcd+8,1);
    CHECK(owner_rtti_window_family(c.object)==0);
    write_word(c.window_bcd+8,old);
    old=read_word(c.window_bcd+12); write_word(c.window_bcd+12,0);
    CHECK(owner_rtti_window_family(c.object)==0);
    write_word(c.window_bcd+12,old);
    old=read_word(c.window_bcd+16); write_word(c.window_bcd+16,4);
    CHECK(owner_rtti_window_family(c.object)==0);
    write_word(c.window_bcd+16,old);

    raw=(BYTE*)(ULONG_PTR)c.leaf_td+8;
    memcpy(saved,raw,sizeof(saved));
    raw[2]='X';
    CHECK(!rtti_name_from_object(c.object,out,sizeof(out),&vr));
    raw[2]=saved[2];
    memset(raw+4,'A',140); /* no @@ terminator within the bounded scan */
    CHECK(!rtti_name_from_object(c.object,out,sizeof(out),&vr));
    restore_name_bytes(c.leaf_td,saved,sizeof(saved));
    CHECK(rtti_name_from_object(c.object,out,sizeof(out),&vr));
    CHECK(!rtti_name_from_object(c.object,out,4,&vr));

    /* Truncating the advertised image at the TypeDescriptor boundary must
       fail before a suffix read, even though the backing array is mapped. */
    g_exe_size=(DWORD)(c.leaf_td-ptr32(image))+14;
    CHECK(!rtti_name_from_object(c.object,out,sizeof(out),&vr));
    g_exe_size=IMAGE_BYTES;
    CHECK(rtti_name_from_object(c.object,out,sizeof(out),&vr));
    puts("PASS: image bounds, signatures, counts, PMDs, pointers, and truncated names fail closed");
}

static void test_admission_requires_live_identity(void) {
    RttiCase c;
    OwnerWindowState *st;
    DWORD old_vtable;
    clear_fixture();
    c=build_case(0,"AnonymousConfirm",1);
    st=owner_state_for(c.object,1);
    CHECK(st && st->object_ptr==c.object && st->vtable_ptr==c.vtable);
    CHECK(owner_state_for(c.object,0)==st);
    old_vtable=objects[0].vtable;
    objects[0].vtable=0x41414141UL;
    CHECK(owner_state_for(c.object,0)==0);
    CHECK(owner_state_for(c.object,1)==0);
    objects[0].vtable=old_vtable;
    CHECK(owner_state_for(c.object,0)==st);
    puts("PASS: admitted generic window state is tied to the live object vtable identity");
}

static void test_admitted_modal_beats_underlying_input(void) {
    RttiCase underlying, modal;
    OwnerWindowState *underlying_state, *modal_state;
    OwnerInputRegion selected;
    POINT point={300,300};
    DWORD candidates=0;

    clear_fixture();
    underlying=build_case(0,"UnderlyingLeaf",1);
    modal=build_case(1,"ConfirmActionLeaf",1);
    underlying_state=owner_state_for(underlying.object,1);
    modal_state=owner_state_for(modal.object,1);
    CHECK(underlying_state && modal_state);
    CHECK(underlying_state->vtable_ptr==underlying.vtable);
    CHECK(modal_state->vtable_ptr==modal.vtable);

    g_ui_present_serial=100;
    g_ui_scale_percent=200;
    memset(g_owner_input_regions,0,sizeof(g_owner_input_regions));
    g_owner_input_regions[0].rect=(UIRectF){100,100,300,300};
    g_owner_input_regions[0].ax=0; g_owner_input_regions[0].ay=0;
    g_owner_input_regions[0].fit_scale=2.0f;
    g_owner_input_regions[0].object_ptr=underlying.object;
    g_owner_input_regions[0].vtable_ptr=underlying_state->vtable_ptr;
    g_owner_input_regions[0].present=100;
    g_owner_input_regions[0].input_order=10;
    g_owner_input_regions[1]=g_owner_input_regions[0];
    g_owner_input_regions[1].ax=200; g_owner_input_regions[1].ay=200;
    g_owner_input_regions[1].object_ptr=modal.object;
    g_owner_input_regions[1].vtable_ptr=modal_state->vtable_ptr;
    g_owner_input_regions[1].input_order=20;
    g_owner_input_region_count=2;

    CHECK(owner_input_select_region(&point,&selected,&candidates));
    CHECK(candidates==2 && selected.object_ptr==modal.object);
    CHECK(selected.vtable_ptr==modal_state->vtable_ptr);
    {
        POINT wrong=point;
        UIRectF button={240,240,260,260};
        /* The old unowned-dialog path used the underlying window's different
           anchor and missed this native child button. */
        CHECK(owner_input_map_region(&wrong,&g_owner_input_regions[0]));
        CHECK(wrong.x==150 && wrong.y==150);
        CHECK(!rect_contains_point(&button,(float)wrong.x,(float)wrong.y));
        CHECK(owner_input_map_region(&point,&selected));
        CHECK(point.x==250 && point.y==250);
        CHECK(rect_contains_point(&button,(float)point.x,(float)point.y));
    }

    /* Removing the modal snapshot restores the underlying owner. A stale
       modal snapshot must have the same result, preventing old confirmation
       rectangles from stealing a later click. */
    g_owner_input_region_count=1;
    point=(POINT){300,300};
    CHECK(owner_input_select_region(&point,&selected,&candidates));
    CHECK(selected.object_ptr==underlying.object);
    g_owner_input_regions[1].present=97;
    g_owner_input_region_count=2;
    point=(POINT){300,300};
    CHECK(owner_input_select_region(&point,&selected,&candidates));
    CHECK(selected.object_ptr==underlying.object && candidates==1);
    puts("PASS: admitted class-free modal region wins over underlying input and stale/modal removal restores the underlying owner");
}

int main(void) {
    test_anonymous_message_families();
    test_balloon_and_explicit_families();
    test_image_bounds_and_invalid_objects();
    test_admission_requires_live_identity();
    test_admitted_modal_beats_underlying_input();
    puts("PASS: RTTI admission 32-bit ASan/UBSan fixture");
    return 0;
}
'''


def main():
    required = (
        "rtti_image_readable", "rtti_type_is", "rtti_name_from_object",
        "owner_rtti_window_family", "owner_object_should_hook", "owner_state_for",
    )
    missing = [name for name in required if f"static " not in SOURCE or
               not re.search(r"^static [^\n]*\b" + re.escape(name) + r"\s*\(", SOURCE, re.M)]
    if missing:
        raise RuntimeError("production RTTI helpers missing: " + ", ".join(missing))

    types = extract_type(SOURCE, "OwnerWindowState") + "\n" + extract_type(SOURCE, "OwnerInputRegion")
    pieces = "\n".join(
        extract_function(SOURCE, name)
        for name in (
            "s_len", "s_contains", "s_equal",
            "owner_class_is_hover_popup", "owner_class_is_world_label",
            "owner_class_is_world_title", "owner_class_is_world_name",
            "owner_class_should_hook", "rtti_image_readable", "rtti_type_is",
            "rtti_name_from_object", "owner_rtti_window_family",
            "owner_object_should_hook", "owner_state_for", "ui_scale_factor",
            "rect_contains_point", "rect_area", "owner_input_region_bounds",
            "owner_input_map_region", "owner_input_select_region",
        )
    )
    code = PREFIX + types + "\n" + STUBS + "\n" + pieces + "\n" + TESTS
    with tempfile.TemporaryDirectory(prefix="prm-rtti-test-") as directory:
        directory_path = Path(directory)
        c_file = directory_path / "rtti_test.c"
        binary = directory_path / "rtti-test"
        c_file.write_text(code)
        compiler = shlex.split(os.environ.get("CC", "clang"))
        flags = [
            "-m32", "-std=c11", "-O1", "-g", "-Wall", "-Wextra", "-Werror",
            "-Wno-unused-function", "-Wno-unused-parameter",
            "-fsanitize=address,undefined", "-fno-sanitize-recover=all",
            "-fno-omit-frame-pointer", str(c_file), "-o", str(binary),
        ]
        subprocess.run(compiler + flags, check=True)
        env = os.environ.copy()
        env.setdefault("ASAN_OPTIONS", "detect_leaks=0")
        subprocess.run([str(binary)], check=True, env=env)
    print("PASS: RTTI admission 32-bit ASan/UBSan harness")


if __name__ == "__main__":
    main()
