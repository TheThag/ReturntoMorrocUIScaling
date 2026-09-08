#!/usr/bin/env python3
"""Exercise the manager's dynamic UIWindow +A0 alternate-background path.

The observed chat window (3440x1440 at 200 percent) has a native rectangle at
(0,983) of 600x96 and a learned anchor at (0,720).  UINewChatWnd emits its
translucent rows and inner frame through vtable slot +A0; that call is separate
from the cached bitmap draw.  This fixture extracts the production registry,
scaler, owner_bitmap_window_draw, and dynamic +A0 wrapper.  Fake 32-bit
vtables provide only the native ABI boundary, so the test does not encode a
class-specific wrapper.
"""

from pathlib import Path
import os
import re
import subprocess
import tempfile

import test_background as background
import test_bitmap as bitmap


ROOT = Path(__file__).resolve().parent


def replace_function(text, name, replacement):
    match = re.search(
        r"^static\s+[^\n]*\b" + re.escape(name) + r"\([^;]*?\)\s*\{",
        text,
        re.M,
    )
    if not match:
        raise RuntimeError(f"missing stub function: {name}")
    depth, end = 1, match.end()
    while depth:
        depth += (text[end] == "{") - (text[end] == "}")
        end += 1
    return text[: match.start()] + replacement + text[end:]


# Reuse the background fixture ABI and its source-extracted registry/scaler.
# The bitmap callback is a native thiscall in the game, so retain that ABI in
# this composed fixture too.
prefix = background.prefix.replace(
    "typedef DWORD (*PFN_BitmapDraw)",
    "typedef DWORD (__attribute__((thiscall)) *PFN_BitmapDraw)",
)
prefix += r"""
typedef DWORD (__attribute__((thiscall)) *PFN_WindowOverlayDraw)(void*);
"""

# Background's normal fixture only knows two small integer identities.  For
# this test those identities are real 32-bit fake object addresses, and their
# first word points at a separate fake vtable.  Unknown objects still exercise
# the forwarding path without being admitted to the owner registry.
stubs = replace_function(
    background.stubs,
    "owner_state_for",
    r"""static OwnerWindowState* owner_state_for(DWORD obj,int create) {
    OwnerWindowState* st=0;
    if(obj==(DWORD)(ULONG_PTR)&known_window) st=&states[1];
    else if(obj==(DWORD)(ULONG_PTR)&second_window) st=&states[2];
    else return 0;
    if(!st->object_ptr && create) {
        st->object_ptr=obj;
        st->vtable_ptr=*(DWORD*)(ULONG_PTR)obj;
        strcpy(st->class_name,obj==(DWORD)(ULONG_PTR)&known_window?
               "UINewChatWnd":"UIItemWnd");
    }
    return st->object_ptr?st:0;
}""",
)

# test_background.production already includes the production bitmap registry,
# queue wrapper, and final scaler.  Add only the two newly exercised scope
# functions; extraction is performed from the current C source at test start.
production = background.production + "\n" + "\n".join(
    bitmap.function(name)
    for name in ("owner_bitmap_window_draw", "owner_alternate_background_scoped")
)


tests = r"""
typedef union { DWORD d[4][8]; float f[4][8]; BYTE bytes[128]; } Quad;
typedef struct { void* verts; DWORD count; } Primitive;
typedef struct {
    DWORD object_ptr,vtable_ptr,thread;
    float ax,ay,fit_scale,offset_x,offset_y;
    int native_size;
} SubmitObservation;

static DWORD chat_vtable[64],other_vtable[64],unknown_vtable[64];
static Quad quads[32];
static Primitive primitives[32];
static SubmitObservation observations[32];
static DWORD observation_count,primitive_cursor;
static DWORD expected_owner,expected_x,expected_y,expected_w,expected_h;
static DWORD expected_cached_calls,chat_calls,other_calls,unknown_calls;

static DWORD __attribute__((thiscall)) native_submit(void* renderer,void* primitive,DWORD flags);
static DWORD __attribute__((thiscall)) native_chat_a0(void* self);
static DWORD __attribute__((thiscall)) native_other_a0(void* self);
static DWORD __attribute__((thiscall)) native_unknown_a0(void* self);
static DWORD __attribute__((thiscall)) native_cached(void* dc,LONG x,LONG y,LONG w,LONG h,DWORD color);

static void quad(Quad* q,float x,float y,float w,float h) {
    DWORD i;
    memset(q,0,sizeof(*q));
    for(i=0;i<4;++i) {
        q->f[i][0]=x+((i&1)?w:0);
        q->f[i][1]=y+((i&2)?h:0);
        q->f[i][2]=0.00001f; q->f[i][3]=0.99999f;
        q->d[i][4]=0xffffffffUL; q->d[i][5]=0xff000000UL;
        q->f[i][6]=(i&1)?1.0f:0.0f;
        q->f[i][7]=(i&2)?1.0f:0.0f;
    }
}

static void native_window_set(NativeWindow* window,DWORD* vt,
                              LONG x,LONG y,LONG w,LONG h) {
    memset(window,0,sizeof(*window));
    *(DWORD*)window->bytes=(DWORD)(ULONG_PTR)vt;
    *(LONG*)(window->bytes+0x14)=w;
    *(LONG*)(window->bytes+0x18)=h;
    *(LONG*)(window->bytes+0x1c)=x;
    *(LONG*)(window->bytes+0x20)=y;
}

static void reset_all(void) {
    memset(&known_window,0,sizeof(known_window));
    memset(&second_window,0,sizeof(second_window));
    memset(&unknown_window,0,sizeof(unknown_window));
    memset(chat_vtable,0,sizeof(chat_vtable));
    memset(other_vtable,0,sizeof(other_vtable));
    memset(unknown_vtable,0,sizeof(unknown_vtable));
    memset(quads,0,sizeof(quads));
    memset(primitives,0,sizeof(primitives));
    memset(observations,0,sizeof(observations));
    memset(states,0,sizeof(states));
    memset(g_owner_bitmap_draws,0,sizeof(g_owner_bitmap_draws));
    memset(&g_owner_bitmap_scope,0,sizeof(g_owner_bitmap_scope));
    g_owner_bitmap_lock=0;
    g_ui_present_serial=100;
    g_owner_bitmap_calls=g_owner_bitmap_submits=g_owner_bitmap_matched=0;
    g_owner_bitmap_overflow=g_owner_bitmap_expired=g_owner_bitmap_mismatched=0;
    g_owner_bitmap_unsupported=g_owner_bitmap_peak=g_owner_bitmap_offscreen=0;
    g_owner_bitmap_unowned=g_owner_bitmap_order=g_owner_bitmap_active_count=0;
    g_owner_bitmap_frame_calls=g_owner_input_order=0;
    g_owner_submit_enabled=g_owner_scale_enabled=g_owner_tooltip_enabled=1;
    g_owner_bitmap_hooks_installed=g_ui_enabled=g_ui_runtime_enabled=1;
    g_ui_scale_global=1;
    g_ui_scale_unmatched=0;
    g_ui_keep_on_screen=1;
    g_ui_screen_w=3440; g_ui_screen_h=1440;
    g_ui_origin_x=g_ui_origin_y=0; g_ui_anchor_mode=1;
    g_ui_global_threshold_percent=75; g_ui_scale_percent=200;
    g_owner_tagged_draws=g_ui_scaled_draws=0;
    unreadable=0; g_GetCurrentThreadId=thread_id;
    observation_count=primitive_cursor=0;
    expected_owner=expected_x=expected_y=expected_w=expected_h=0;
    expected_cached_calls=chat_calls=other_calls=unknown_calls=0;
    g_owner_bitmap_submit=native_submit;
    chat_vtable[0xa0/4]=(DWORD)(ULONG_PTR)(void*)native_chat_a0;
    other_vtable[0xa0/4]=(DWORD)(ULONG_PTR)(void*)native_other_a0;
    unknown_vtable[0xa0/4]=(DWORD)(ULONG_PTR)(void*)native_unknown_a0;
}

static OwnerWindowState* chat_state(void) {
    OwnerWindowState* st;
    *(DWORD*)known_window.bytes=(DWORD)(ULONG_PTR)chat_vtable;
    st=owner_state_for((DWORD)(ULONG_PTR)&known_window,1);
    CHECK(st);
    /* This is the observed retained native anchor from the 3E F8 sample. */
    st->have_anchor=1; st->ax=0.0f; st->ay=720.0f;
    return st;
}

static void submit_rect(float x,float y,float w,float h,DWORD flags) {
    Quad* q; Primitive* p;
    CHECK(primitive_cursor<32);
    q=&quads[primitive_cursor]; p=&primitives[primitive_cursor];
    quad(q,x,y,w,h); p->verts=q; p->count=4;
    ++primitive_cursor;
    owner_bitmap_queue_scoped((void*)(ULONG_PTR)0x1234,p,flags);
}

static DWORD __attribute__((thiscall)) native_submit(void* renderer,void* primitive,DWORD flags) {
    Primitive* p=(Primitive*)primitive;
    CHECK(renderer==(void*)(ULONG_PTR)0x1234);
    CHECK(p && p->count==4 && p->verts);
    CHECK(observation_count<32);
    observations[observation_count].object_ptr=g_owner_bitmap_scope.object_ptr;
    observations[observation_count].vtable_ptr=g_owner_bitmap_scope.vtable_ptr;
    observations[observation_count].thread=g_owner_bitmap_scope.thread;
    observations[observation_count].ax=g_owner_bitmap_scope.ax;
    observations[observation_count].ay=g_owner_bitmap_scope.ay;
    observations[observation_count].fit_scale=g_owner_bitmap_scope.fit_scale;
    observations[observation_count].offset_x=g_owner_bitmap_scope.offset_x;
    observations[observation_count].offset_y=g_owner_bitmap_scope.offset_y;
    observations[observation_count].native_size=g_owner_bitmap_scope.native_size;
    ++observation_count;
    (void)flags;
    return 0;
}

static void window_geometry(void* self,LONG* x,LONG* y,LONG* w,LONG* h) {
    NativeWindow* window=(NativeWindow*)self;
    *w=*(LONG*)(window->bytes+0x14);
    *h=*(LONG*)(window->bytes+0x18);
    *x=*(LONG*)(window->bytes+0x1c);
    *y=*(LONG*)(window->bytes+0x20);
}

static DWORD __attribute__((thiscall)) native_chat_a0(void* self) {
    LONG x,y,w,h;
    CHECK(self==(void*)&known_window);
    window_geometry(self,&x,&y,&w,&h);
    /* UINewChatWnd's direct path emits row/frame rectangles separately. */
    submit_rect((float)x+4.0f,(float)y+1.0f,(float)w-8.0f,20.0f,0xa001);
    submit_rect((float)x+4.0f,(float)y+1.0f,(float)w-8.0f,(float)h-1.0f,0xa002);
    ++chat_calls;
    return 0xC0A70001UL;
}

static DWORD __attribute__((thiscall)) native_other_a0(void* self) {
    LONG x,y,w,h;
    CHECK(self==(void*)&second_window);
    window_geometry(self,&x,&y,&w,&h);
    submit_rect((float)x+2.0f,(float)y+2.0f,(float)w-4.0f,(float)h-4.0f,0xb001);
    ++other_calls;
    return 0xC0A70002UL;
}

static DWORD __attribute__((thiscall)) native_unknown_a0(void* self) {
    LONG x,y,w,h;
    CHECK(self==(void*)&unknown_window);
    /* owner_bitmap_window_draw must clear an inherited owner before an
       unrecognized object forwards into its dynamic +A0 implementation. */
    CHECK(!g_owner_bitmap_scope.object_ptr && !g_owner_bitmap_scope.thread);
    window_geometry(self,&x,&y,&w,&h);
    submit_rect((float)x,(float)y,(float)w,(float)h,0xc001);
    ++unknown_calls;
    return 0xC0A70003UL;
}

static DWORD __attribute__((thiscall)) native_cached(void* dc,LONG x,LONG y,
                                                     LONG w,LONG h,DWORD color) {
    CHECK(dc==(void*)(ULONG_PTR)0x3456);
    CHECK((DWORD)x==expected_x && (DWORD)y==expected_y &&
          (DWORD)w==expected_w && (DWORD)h==expected_h);
    CHECK(color==0xff123456UL);
    CHECK(g_owner_bitmap_scope.object_ptr==expected_owner);
    submit_rect((float)x,(float)y,(float)w,(float)h,0xd001);
    ++expected_cached_calls;
    return 0xC0A70004UL;
}

static void assert_observation(const SubmitObservation* a,
                               const SubmitObservation* b) {
    CHECK(a->object_ptr==b->object_ptr && a->vtable_ptr==b->vtable_ptr);
    CHECK(a->thread==b->thread && a->native_size==b->native_size);
    CHECK(fabsf(a->ax-b->ax)<0.001f && fabsf(a->ay-b->ay)<0.001f);
    CHECK(fabsf(a->fit_scale-b->fit_scale)<0.001f);
    CHECK(fabsf(a->offset_x-b->offset_x)<0.001f &&
          fabsf(a->offset_y-b->offset_y)<0.001f);
}

static void assert_chat_transform(DWORD first,DWORD count) {
    DWORD i;
    CHECK(count==3);
    for(i=first;i<first+count;++i) {
        CHECK(observations[i].object_ptr==(DWORD)(ULONG_PTR)&known_window);
        CHECK(observations[i].vtable_ptr==(DWORD)(ULONG_PTR)chat_vtable);
        CHECK(observations[i].thread==17);
        CHECK(fabsf(observations[i].ax-0.0f)<0.001f);
        CHECK(fabsf(observations[i].ay-720.0f)<0.001f);
        CHECK(fabsf(observations[i].fit_scale-2.0f)<0.001f);
        CHECK(fabsf(observations[i].offset_x)<0.001f &&
              fabsf(observations[i].offset_y)<0.001f);
        if(i>first) assert_observation(&observations[first],&observations[i]);
    }
}

static void assert_scaled(DWORD primitive_index,DWORD observation_index,
                          float x,float y,float w,float h) {
    Quad out; Quad* in=&quads[primitive_index];
    const SubmitObservation* obs=&observations[observation_index];
    DWORD i;
    CHECK(make_scaled_ui_vertices(5,0x1c4,in,4,out.bytes,sizeof(out),0,0)==&out);
    for(i=0;i<4;++i) {
        float sx=x+((i&1)?w:0), sy=y+((i&2)?h:0);
        CHECK(fabsf(out.f[i][0]-(obs->ax+(sx-obs->ax)*obs->fit_scale+obs->offset_x))<0.001f);
        CHECK(fabsf(out.f[i][1]-(obs->ay+(sy-obs->ay)*obs->fit_scale+obs->offset_y))<0.001f);
    }
}

static DWORD render_chat(LONG x,LONG y,LONG w,LONG h) {
    DWORD first=observation_count;
    NativeWindow* window=&known_window;
    native_window_set(window,chat_vtable,x,y,w,h);
    expected_owner=(DWORD)(ULONG_PTR)window;
    expected_x=(DWORD)x; expected_y=(DWORD)y;
    expected_w=(DWORD)w; expected_h=(DWORD)h;
    CHECK(owner_alternate_background_scoped(window)==0xC0A70001UL);
    CHECK(owner_bitmap_draw_c((DWORD)(ULONG_PTR)window,
          (void*)(ULONG_PTR)0x3456,(void*)native_cached,x,y,w,h,0xff123456UL)==
          0xC0A70004UL);
    CHECK(chat_calls && expected_cached_calls);
    return first;
}

static void observed_chat_frame(void) {
    DWORD first,i;
    reset_all(); chat_state();
    first=render_chat(0,983,600,96);
    CHECK(observation_count==first+3);
    assert_chat_transform(first,3);
    CHECK(quads[first].f[0][0]==4.0f && quads[first].f[0][1]==984.0f);
    CHECK(quads[first+1].f[0][0]==4.0f && quads[first+1].f[0][1]==984.0f);
    CHECK(quads[first+2].f[0][0]==0.0f && quads[first+2].f[0][1]==983.0f);
    /* All three direct/cached submissions carry the same frozen owner record. */
    for(i=0;i<3;++i) assert_scaled(first+i,first+i,
        i==2?0.0f:4.0f,i==2?983.0f:984.0f,
        i==2?600.0f:592.0f,i==0?20.0f:(i==1?95.0f:96.0f));
    CHECK(g_owner_bitmap_active_count==0);
    CHECK(g_owner_bitmap_unowned==0 && !g_owner_bitmap_mismatched);
}

static void resize_preserves_delayed_queue(void) {
    DWORD old_first,new_first,back_first,i;
    reset_all(); chat_state();

    /* The old 600x250 frame is queued at the same retained (0,720) anchor. */
    old_first=render_chat(0,829,600,250);
    CHECK(observation_count==old_first+3);
    assert_chat_transform(old_first,3);
    /* Native layout changes before the GPU-side queue is consumed.  Registry
       entries must retain the old transform snapshot, independent of this
       mutable object geometry. */
    native_window_set(&known_window,chat_vtable,0,983,600,96);
    g_ui_present_serial+=1;
    for(i=0;i<3;++i) {
        CHECK(owner_bitmap_consume_transform(0x1c4,&quads[old_first+i],4,
              &observations[old_first+i].ax,&observations[old_first+i].ay,
              &observations[old_first+i].fit_scale,
              &observations[old_first+i].offset_x,
              &observations[old_first+i].offset_y)==1);
        CHECK(fabsf(observations[old_first+i].ax)<0.001f &&
              fabsf(observations[old_first+i].ay-720.0f)<0.001f);
    }
    CHECK(g_owner_bitmap_active_count==0);

    /* New 600x96 and return-to-250 frames must reuse that same learned anchor,
       even though choose_group_anchor would otherwise pick the bottom edge. */
    new_first=render_chat(0,983,600,96);
    CHECK(observation_count==new_first+3);
    assert_chat_transform(new_first,3);
    for(i=0;i<3;++i) CHECK(owner_bitmap_consume_transform(0x1c4,
        &quads[new_first+i],4,&observations[new_first+i].ax,
        &observations[new_first+i].ay,&observations[new_first+i].fit_scale,
        &observations[new_first+i].offset_x,&observations[new_first+i].offset_y)==1);
    back_first=render_chat(0,829,600,250);
    CHECK(observation_count==back_first+3);
    assert_chat_transform(back_first,3);
    for(i=0;i<3;++i) CHECK(owner_bitmap_consume_transform(0x1c4,
        &quads[back_first+i],4,&observations[back_first+i].ax,
        &observations[back_first+i].ay,&observations[back_first+i].fit_scale,
        &observations[back_first+i].offset_x,&observations[back_first+i].offset_y)==1);
    CHECK(g_owner_bitmap_active_count==0);
}

static void different_class_same_slot(void) {
    DWORD first;
    OwnerBitmapScope outer;
    reset_all();
    native_window_set(&second_window,other_vtable,2200,200,120,80);
    expected_owner=(DWORD)(ULONG_PTR)&second_window;
    first=observation_count;
    CHECK(owner_alternate_background_scoped(&second_window)==0xC0A70002UL);
    CHECK(other_calls==1 && observation_count==first+1);
    CHECK(observations[first].object_ptr==expected_owner);
    CHECK(observations[first].vtable_ptr==(DWORD)(ULONG_PTR)other_vtable);
    CHECK(fabsf(observations[first].fit_scale-2.0f)<0.001f);
    CHECK(g_owner_bitmap_active_count==1);
    CHECK(owner_bitmap_consume_transform(0x1c4,&quads[primitive_cursor-1],4,
          &observations[first].ax,&observations[first].ay,
          &observations[first].fit_scale,&observations[first].offset_x,
          &observations[first].offset_y)==1);
    CHECK(!g_owner_bitmap_active_count);
    outer=g_owner_bitmap_scope;
    CHECK(!memcmp(&outer,&g_owner_bitmap_scope,sizeof(outer)));
}

static void unknown_forwards_and_restores(void) {
    OwnerBitmapScope outer;
    DWORD before;
    reset_all();
    native_window_set(&unknown_window,unknown_vtable,900,400,260,120);
    outer.object_ptr=0x10203040UL; outer.vtable_ptr=0x50607080UL;
    outer.thread=17; outer.ax=11.0f; outer.ay=22.0f;
    outer.fit_scale=1.5f; outer.offset_x=3.0f; outer.offset_y=4.0f;
    outer.native_size=0; g_owner_bitmap_scope=outer;
    before=observation_count;
    CHECK(owner_alternate_background_scoped(&unknown_window)==0xC0A70003UL);
    CHECK(unknown_calls==1 && observation_count==before+1);
    CHECK(observations[before].object_ptr==0 && observations[before].thread==0);
    CHECK(g_owner_bitmap_unowned==1 && !g_owner_bitmap_active_count);
    CHECK(!memcmp(&outer,&g_owner_bitmap_scope,sizeof(outer)));
    CHECK(owner_alternate_background_scoped(0)==0);
    CHECK(!memcmp(&outer,&g_owner_bitmap_scope,sizeof(outer)));
}

int main(void) {
    CHECK(sizeof(void*)==4 && sizeof(Primitive)==8);
    observed_chat_frame();
    resize_preserves_delayed_queue();
    different_class_same_slot();
    unknown_forwards_and_restores();
    puts("PASS chat +A0 ownership: native 3440x1440/200% 600x96 frame, retained (0,720) anchor across 600x250 resize and delayed queue, direct row/inner/cached transform identity, dynamic different-class vtable dispatch, and unknown forwarding/restoration");
    return 0;
}
"""


def main():
    with tempfile.TemporaryDirectory(prefix="prm-chat-background-test-") as directory:
        c_file = Path(directory) / "chat_background_test.c"
        binary = Path(directory) / "chat_background_test"
        c_file.write_text(prefix + bitmap.types + stubs + production + tests)
        subprocess.run(
            [
                os.environ.get("CC", "clang"),
                "-m32",
                "-std=c11",
                "-O1",
                "-g",
                "-Wall",
                "-Wextra",
                "-Wno-unused-variable",
                "-Wno-unused-parameter",
                "-Wno-unused-function",
                "-fsanitize=address,undefined",
                "-fno-omit-frame-pointer",
                str(c_file),
                "-o",
                str(binary),
            ],
            check=True,
        )
        subprocess.run([str(binary)], check=True)


if __name__ == "__main__":
    main()
