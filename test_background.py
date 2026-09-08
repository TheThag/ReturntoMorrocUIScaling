#!/usr/bin/env python3
"""Exercise the native UIWindow background scope and bitmap provenance.

The real background call is a cdecl five argument rectangle renderer.  This
test extracts the production scope wrapper, queue registry, and final vertex
scaler, then calls them through 32-bit fake native windows.  The fake objects
only stand in for the native object/RTTI lookup; all scope, registry, and
scaling behavior is production code.
"""

from pathlib import Path
import os
import re
import subprocess
import tempfile

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


prefix = bitmap.prefix.replace("#define WINAPI\n", "#define WINAPI __attribute__((stdcall))\n")
prefix += r"""
typedef DWORD (__attribute__((thiscall)) *PFN_SpriteSubmit)(void*,void*,DWORD);
typedef DWORD (*PFN_WindowBackgroundDraw)(LONG,LONG,LONG,LONG,DWORD);
typedef struct { BYTE bytes[64]; } NativeWindow;
static NativeWindow known_window, second_window, unknown_window;
"""


stubs = bitmap.stubs
stubs = replace_function(
    stubs,
    "owner_state_for",
    r"""static OwnerWindowState* owner_state_for(DWORD obj,int create) {
    OwnerWindowState* st=0;
    if(obj==(DWORD)(ULONG_PTR)&known_window) st=&states[1];
    else if(obj==(DWORD)(ULONG_PTR)&second_window) st=&states[2];
    else return 0;
    if(!st->object_ptr && create) {
        st->object_ptr=obj;
        st->vtable_ptr=obj^0x12345678UL;
        strcpy(st->class_name,"UIItemWnd");
    }
    return st->object_ptr?st:0;
}""",
)
stubs += r"""
static PFN_SpriteSubmit g_owner_bitmap_submit;
static PFN_WindowBackgroundDraw g_owner_background_draw;
"""


production = "\n".join(
    bitmap.function(name)
    for name in (
        "f_abs",
        "fvf_stride",
        "ui_scale_factor",
        "rect_is_global",
        "choose_group_anchor",
        "owner_class_is_hover_popup",
        "owner_class_is_world_label",
        "owner_class_is_world_title",
        "owner_class_is_world_name",
        "owner_class_should_hook",
        "owner_input_touch_state",
        "owner_fit_rect",
        "owner_bitmap_prepare",
        "owner_bitmap_draw_c",
        "owner_background_draw_c",
        "owner_bitmap_registry_lock",
        "owner_bitmap_registry_unlock",
        "owner_bitmap_bucket",
        "owner_bitmap_forget",
        "owner_bitmap_note_vertices",
        "owner_bitmap_consume_transform",
        "owner_bitmap_consume_vertices",
        "looks_like_ui_vertices",
        "make_scaled_ui_vertices",
        "owner_bitmap_queue_scoped",
    )
)


tests = r"""
typedef union { DWORD d[4][8]; float f[4][8]; BYTE bytes[128]; } Quad;
typedef struct { void* verts; DWORD count; } Primitive;

static Quad box_quad,text_left,text_right,nested_quad,unknown_quad,parent_quad;
static Primitive box_primitive,left_primitive,right_primitive,nested_primitive;
static Primitive unknown_primitive,parent_primitive;
static DWORD expected_primitive,submit_calls,background_calls,bitmap_calls;
static DWORD expected_x,expected_y,expected_w,expected_h,expected_color;
static DWORD expected_owner;
static DWORD background_return,bitmap_return;
static DWORD __attribute__((thiscall)) native_submit(void*,void*,DWORD);
static DWORD native_background(LONG,LONG,LONG,LONG,DWORD);

static void native_window_set(NativeWindow* window,LONG x,LONG y,LONG w,LONG h) {
    *(LONG*)(window->bytes+0x14)=w;
    *(LONG*)(window->bytes+0x18)=h;
    *(LONG*)(window->bytes+0x1c)=x;
    *(LONG*)(window->bytes+0x20)=y;
}

static void reset_all(void) {
    memset(&known_window,0,sizeof(known_window));
    memset(&second_window,0,sizeof(second_window));
    memset(&unknown_window,0,sizeof(unknown_window));
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
    g_ui_scale_global=1; g_ui_scale_unmatched=0;
    g_ui_keep_on_screen=1;
    g_ui_screen_w=1920; g_ui_screen_h=1080;
    g_ui_origin_x=g_ui_origin_y=0; g_ui_anchor_mode=1;
    g_ui_global_threshold_percent=75; g_ui_scale_percent=150;
    g_owner_tagged_draws=g_ui_scaled_draws=0;
    unreadable=0; g_GetCurrentThreadId=thread_id;
    expected_primitive=submit_calls=background_calls=bitmap_calls=0;
    expected_x=expected_y=expected_w=expected_h=expected_color=0;
    expected_owner=0; background_return=0xBADC0DE1; bitmap_return=0xBADC0DE2;
    g_owner_bitmap_submit=native_submit;
    g_owner_background_draw=native_background;
}

static void quad(Quad* q,float x,float y,float w,float h) {
    DWORD i;
    memset(q,0,sizeof(*q));
    for(i=0;i<4;++i) {
        q->f[i][0]=x+((i&1)?w:0);
        q->f[i][1]=y+((i&2)?h:0);
        q->f[i][2]=0.00001f; q->f[i][3]=0.99999f;
        q->d[i][4]=0xffffffff; q->d[i][5]=0xff000000;
        q->f[i][6]=(i&1)?1:0; q->f[i][7]=(i&2)?1:0;
    }
}

static void submit_primitive(Primitive* primitive) {
    expected_primitive=(DWORD)(ULONG_PTR)primitive;
    owner_bitmap_queue_scoped((void*)(ULONG_PTR)0x1234,primitive,0x201);
}

static DWORD __attribute__((thiscall)) native_submit(void* renderer,void* primitive,DWORD flags) {
    CHECK(renderer==(void*)(ULONG_PTR)0x1234);
    CHECK(flags==0x201);
    CHECK((DWORD)(ULONG_PTR)primitive==expected_primitive);
    ++submit_calls;
    return 0;
}

static DWORD native_background(LONG x,LONG y,LONG w,LONG h,DWORD color) {
    CHECK(x==(LONG)expected_x && y==(LONG)expected_y);
    CHECK(w==(LONG)expected_w && h==(LONG)expected_h && color==expected_color);
    if(expected_owner==(DWORD)(ULONG_PTR)&known_window ||
       expected_owner==(DWORD)(ULONG_PTR)&second_window)
        CHECK(g_owner_bitmap_scope.object_ptr==expected_owner);
    else CHECK(!g_owner_bitmap_scope.object_ptr && !g_owner_bitmap_scope.thread);
    ++background_calls;
    if(expected_owner==(DWORD)(ULONG_PTR)&known_window) submit_primitive(&box_primitive);
    else if(expected_owner==(DWORD)(ULONG_PTR)&second_window) submit_primitive(&nested_primitive);
    else {
        /* Unknown/unreadable owners must not borrow the enclosing scope. */
        submit_primitive(&unknown_primitive);
    }
    return background_return;
}

static DWORD native_bitmap(void* dc,LONG x,LONG y,LONG w,LONG h,DWORD color) {
    CHECK(dc==(void*)(ULONG_PTR)0x3456);
    CHECK(x==(LONG)expected_x && y==(LONG)expected_y);
    CHECK(w==(LONG)expected_w && h==(LONG)expected_h && color==expected_color);
    CHECK(g_owner_bitmap_scope.object_ptr==expected_owner);
    ++bitmap_calls;
    submit_primitive(&left_primitive);
    submit_primitive(&right_primitive);
    return bitmap_return;
}

static void transformed(const Quad* original,const Quad* out,float ax,float ay,
                        float scale,float dx,float dy) {
    DWORD i,j;
    for(i=0;i<4;++i) {
        CHECK(fabsf(out->f[i][0]-(ax+(original->f[i][0]-ax)*scale+dx))<0.001f);
        CHECK(fabsf(out->f[i][1]-(ay+(original->f[i][1]-ay)*scale+dy))<0.001f);
        for(j=2;j<8;++j) CHECK(out->d[i][j]==original->d[i][j]);
    }
}

static const void* scaled(Quad* in,Quad* out) {
    return make_scaled_ui_vertices(5,0x1c4,in,4,out->bytes,sizeof(*out),0,0);
}

static void background_and_bitmap_share_transform(void) {
    DWORD percent,kind;
    const char* classes[]={"UIItemWnd","UITransBalloonText","UICharInfoBalloonText"};
    for(kind=0;kind<3;++kind) for(percent=150;percent<=200;percent+=50) {
        OwnerBitmapScope outer,text_scope;
        float box_ax,box_ay,box_scale,box_dx,box_dy;
        float text_ax,text_ay,text_scale,text_dx,text_dy;
        Quad box_out,left_out,right_out;
        reset_all(); g_ui_scale_percent=(int)percent;
        native_window_set(&known_window,120,140,400,200);
        strcpy(owner_state_for((DWORD)(ULONG_PTR)&known_window,1)->class_name,classes[kind]);
        expected_x=120; expected_y=140; expected_w=400; expected_h=200;
        expected_color=0xff345678; expected_owner=(DWORD)(ULONG_PTR)&known_window;
        box_primitive.verts=&box_quad; box_primitive.count=4;
        left_primitive.verts=&text_left; left_primitive.count=4;
        right_primitive.verts=&text_right; right_primitive.count=4;
        quad(&box_quad,120,140,400,200);
        quad(&text_left,120,140,256,200);
        quad(&text_right,376,140,144,200);

        /* This is the first draw of the object: no earlier bitmap scope may be
           required for the direct background rectangle to acquire ownership. */
        outer=g_owner_bitmap_scope;
        CHECK(owner_background_draw_c(expected_owner,expected_x,expected_y,
                                      expected_w,expected_h,expected_color)==background_return);
        CHECK(background_calls==1 && submit_calls==1);
        CHECK(!memcmp(&g_owner_bitmap_scope,&outer,sizeof(outer)));
        CHECK(g_owner_bitmap_active_count==1);
        CHECK(owner_bitmap_consume_transform(0x1c4,&box_quad,4,&box_ax,&box_ay,
                                             &box_scale,&box_dx,&box_dy)==1);
        /* The tag was consumed above; requeue and verify the real scaler. */
        owner_bitmap_prepare(expected_owner,expected_x,expected_y,expected_w,expected_h);
        owner_bitmap_note_vertices(&box_quad,4,&g_owner_bitmap_scope);
        CHECK(scaled(&box_quad,&box_out)==&box_out);
        transformed(&box_quad,&box_out,box_ax,box_ay,box_scale,box_dx,box_dy);
        /* The real manager enters the cached bitmap draw after the direct
           background call has returned; restore the enclosing (empty) scope
           after this explicit requeue check. */
        g_owner_bitmap_scope=outer;

        /* The cached text is submitted by the separate bitmap wrapper, but it
           must retain the same live owner transform as the direct box. */
        CHECK(owner_bitmap_draw_c(expected_owner,(void*)(ULONG_PTR)0x3456,
                                  (void*)native_bitmap,expected_x,expected_y,
                                  expected_w,expected_h,expected_color)==bitmap_return);
        CHECK(bitmap_calls==1 && submit_calls==3);
        CHECK(!g_owner_bitmap_scope.object_ptr && !g_owner_bitmap_scope.thread);
        owner_bitmap_consume_transform(0x1c4,&text_left,4,&text_ax,&text_ay,
                                       &text_scale,&text_dx,&text_dy);
        owner_bitmap_consume_transform(0x1c4,&text_right,4,&text_ax,&text_ay,
                                       &text_scale,&text_dx,&text_dy);
        CHECK(fabsf(text_ax-box_ax)<0.001f && fabsf(text_ay-box_ay)<0.001f);
        CHECK(fabsf(text_scale-box_scale)<0.001f);
        CHECK(fabsf(text_dx-box_dx)<0.001f && fabsf(text_dy-box_dy)<0.001f);
        CHECK(g_owner_bitmap_active_count==0);

        /* Exercise the same transform through the final scaler on the two
           text tiles after retagging, ensuring the box and both tiles align. */
        owner_bitmap_prepare(expected_owner,expected_x,expected_y,expected_w,expected_h);
        owner_bitmap_note_vertices(&text_left,4,&g_owner_bitmap_scope);
        owner_bitmap_note_vertices(&text_right,4,&g_owner_bitmap_scope);
        text_scope=g_owner_bitmap_scope;
        CHECK(scaled(&text_left,&left_out)==&left_out);
        CHECK(scaled(&text_right,&right_out)==&right_out);
        transformed(&text_left,&left_out,text_scope.ax,text_scope.ay,
                    text_scope.fit_scale,text_scope.offset_x,text_scope.offset_y);
        transformed(&text_right,&right_out,text_scope.ax,text_scope.ay,
                    text_scope.fit_scale,text_scope.offset_x,text_scope.offset_y);
        CHECK(fabsf(left_out.f[1][0]-right_out.f[0][0])<0.001f);
        CHECK(g_owner_bitmap_active_count==0);
    }
}

static void nested_scope_restores_outer(void) {
    OwnerBitmapScope outer;
    Quad nested_out,parent_out;
    float ax,ay,s,dx,dy;
    reset_all();
    native_window_set(&known_window,100,100,300,180);
    native_window_set(&second_window,700,240,240,120);
    box_primitive.verts=&box_quad; box_primitive.count=4;
    nested_primitive.verts=&nested_quad; nested_primitive.count=4;
    parent_primitive.verts=&parent_quad; parent_primitive.count=4;
    quad(&box_quad,100,100,300,180); quad(&nested_quad,700,240,240,120);
    quad(&parent_quad,100,100,300,180);
    CHECK(owner_bitmap_prepare((DWORD)(ULONG_PTR)&known_window,100,100,300,180));
    outer=g_owner_bitmap_scope;
    expected_owner=(DWORD)(ULONG_PTR)&second_window;
    expected_x=700; expected_y=240; expected_w=240; expected_h=120;
    expected_color=0xff001122;
    CHECK(owner_background_draw_c(expected_owner,expected_x,expected_y,
                                  expected_w,expected_h,expected_color)==background_return);
    CHECK(!memcmp(&g_owner_bitmap_scope,&outer,sizeof(outer)));
    CHECK(g_owner_bitmap_unowned==0);
    owner_bitmap_consume_transform(0x1c4,&nested_quad,4,&ax,&ay,&s,&dx,&dy);
    CHECK(fabsf(ax-outer.ax)>0.1f || fabsf(ay-outer.ay)>0.1f || s!=outer.fit_scale);
    CHECK(owner_bitmap_consume_transform(0x1c4,&nested_quad,4,&ax,&ay,&s,&dx,&dy)==0);
    /* The enclosing scope can still own a later queue after nested return. */
    owner_bitmap_note_vertices(&parent_quad,4,&outer);
    CHECK(scaled(&parent_quad,&parent_out)==&parent_out);
    transformed(&parent_quad,&parent_out,outer.ax,outer.ay,outer.fit_scale,
                outer.offset_x,outer.offset_y);
    CHECK(g_owner_bitmap_active_count==0);
    (void)nested_out;
}

static void unknown_and_unreadable_do_not_borrow_parent(void) {
    OwnerBitmapScope outer;
    Quad unknown_out,parent_out;
    float ax,ay,s,dx,dy;
    reset_all();
    native_window_set(&known_window,200,120,320,160);
    native_window_set(&unknown_window,900,400,260,120);
    box_primitive.verts=&box_quad; box_primitive.count=4;
    unknown_primitive.verts=&unknown_quad; unknown_primitive.count=4;
    parent_primitive.verts=&parent_quad; parent_primitive.count=4;
    quad(&box_quad,200,120,320,160); quad(&unknown_quad,900,400,260,120);
    quad(&parent_quad,200,120,320,160);
    CHECK(owner_bitmap_prepare((DWORD)(ULONG_PTR)&known_window,200,120,320,160));
    outer=g_owner_bitmap_scope;
    expected_owner=(DWORD)(ULONG_PTR)&unknown_window;
    expected_x=9; expected_y=8; expected_w=260; expected_h=120;
    expected_color=0xff998877;
    CHECK(owner_background_draw_c(expected_owner,expected_x,expected_y,
                                  expected_w,expected_h,expected_color)==background_return);
    CHECK(background_calls==1 && submit_calls==1);
    CHECK(g_owner_bitmap_unowned==1);
    CHECK(!memcmp(&g_owner_bitmap_scope,&outer,sizeof(outer)));
    CHECK(make_scaled_ui_vertices(5,0x1c4,&unknown_quad,4,unknown_out.bytes,
                                  sizeof(unknown_out),0,0)==&unknown_quad);
    CHECK(!g_owner_bitmap_active_count);

    /* An unreadable native geometry block still forwards the exact original
       arguments and leaves the enclosing owner scope intact. */
    unreadable=(BYTE*)&unknown_window+0x14;
    CHECK(owner_background_draw_c(expected_owner,expected_x,expected_y,
                                  expected_w,expected_h,expected_color)==background_return);
    unreadable=0;
    CHECK(background_calls==2 && submit_calls==2);
    CHECK(!memcmp(&g_owner_bitmap_scope,&outer,sizeof(outer)));
    CHECK(g_owner_bitmap_unowned==2);

    owner_bitmap_note_vertices(&parent_quad,4,&outer);
    CHECK(owner_bitmap_consume_transform(0x1c4,&parent_quad,4,&ax,&ay,&s,&dx,&dy)==1);
    owner_bitmap_note_vertices(&parent_quad,4,&outer);
    CHECK(scaled(&parent_quad,&parent_out)==&parent_out);
    transformed(&parent_quad,&parent_out,ax,ay,s,dx,dy);
    CHECK(g_owner_bitmap_active_count==0);
}

int main(void) {
    CHECK(sizeof(void*)==4 && sizeof(Primitive)==8);
    background_and_bitmap_share_transform();
    nested_scope_restores_outer();
    unknown_and_unreadable_do_not_borrow_parent();
    puts("PASS background ownership: first-draw direct box and cached text share 150/200% transforms, tiled registry provenance, nested restoration, unknown/unreadable forwarding, and parent-scope isolation");
    return 0;
}
"""


def main():
    with tempfile.TemporaryDirectory(prefix="prm-background-test-") as directory:
        c_file = Path(directory) / "background_test.c"
        binary = Path(directory) / "background_test"
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
