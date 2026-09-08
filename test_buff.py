#!/usr/bin/env python3
"""Exercise exact native buff provenance and queued box/text scaling on i386."""
from pathlib import Path
import os
import subprocess
import tempfile
import test_background as background
import test_bitmap as bitmap

prefix = background.prefix + r'''
typedef DWORD (__attribute__((thiscall)) *PFN_BuffHover)(void*,LONG,LONG);
static PFN_BuffHover g_owner_buff_hover;
static DWORD g_owner_buff_scene,g_owner_buff_scene_vtable,g_owner_buff_object,g_owner_buff_vtable;
'''
stubs = background.replace_function(background.stubs, 'owner_is_buff_tooltip',
                                    'static int owner_is_buff_tooltip(DWORD);')
stubs = background.replace_function(stubs, 'owner_buff_popup_offset',
                                    'static void owner_buff_popup_offset(OwnerWindowState*,LONG,LONG,LONG);')
helpers = '\n'.join(bitmap.function(n) for n in
                    ('owner_buff_hover_scoped','owner_is_buff_tooltip','owner_buff_popup_offset'))
tests = background.tests.replace('int main(void)', 'int background_baseline(void)') + r'''
static BYTE scene[0x5ec];
static DWORD hover_calls,hover_popup;
static DWORD __attribute__((thiscall)) native_hover(void* self,LONG x,LONG y) {
    CHECK(self==scene && x==3420 && y==180);
    ++hover_calls; *(DWORD*)((BYTE*)self+0x5e8)=hover_popup;
    return 0xabcdef01UL;
}
static void attach_buff(void) {
    memset(scene,0,sizeof(scene)); *(DWORD*)scene=0x12345000;
    *(DWORD*)&known_window=0x12346000;
    hover_popup=(DWORD)(ULONG_PTR)&known_window;
    g_owner_buff_hover=native_hover;
    CHECK(owner_buff_hover_scoped(scene,3420,180)==0xabcdef01UL);
    CHECK(owner_is_buff_tooltip(hover_popup));
}
static void exact_identity(void) {
    reset_all(); hover_calls=0; attach_buff(); CHECK(hover_calls==1);
    CHECK(!owner_is_buff_tooltip(0));
    CHECK(!owner_is_buff_tooltip((DWORD)(ULONG_PTR)&second_window));
    *(DWORD*)scene^=4; CHECK(!owner_is_buff_tooltip(hover_popup)); *(DWORD*)scene^=4;
    *(DWORD*)&known_window^=4; CHECK(!owner_is_buff_tooltip(hover_popup)); *(DWORD*)&known_window^=4;
    *(DWORD*)(scene+0x5e8)=0; CHECK(!owner_is_buff_tooltip(hover_popup));
    *(DWORD*)(scene+0x5e8)=hover_popup;
    unreadable=scene; CHECK(!owner_is_buff_tooltip(hover_popup)); unreadable=0;
    unreadable=scene+0x5e8; CHECK(!owner_is_buff_tooltip(hover_popup)); unreadable=0;
    unreadable=&known_window; CHECK(!owner_is_buff_tooltip(hover_popup)); unreadable=0;
    CHECK(owner_is_buff_tooltip(hover_popup));
    hover_popup=0; CHECK(owner_buff_hover_scoped(scene,3420,180)==0xabcdef01UL);
    CHECK(!g_owner_buff_object && !g_owner_buff_scene);
    g_owner_buff_hover=0;
    CHECK(owner_buff_hover_scoped(0,1,2)==0 && !g_owner_buff_object);
}
static void buff_box_and_text(void) {
    int percent,entry; Quad box,left,right; OwnerWindowState* st;
    for(percent=150;percent<=200;percent+=50) for(entry=0;entry<3;++entry) {
        float scale=(float)percent/100.0f,expected_left,expected_top,expected_right;
        reset_all(); attach_buff(); g_ui_screen_w=3440; g_ui_screen_h=1440;
        g_ui_scale_percent=percent; g_ui_anchor_mode=1; g_ui_scale_global=0;
        expected_x=3246; expected_y=171+35*entry; expected_w=146; expected_h=106;
        expected_color=0xff345678; expected_owner=(DWORD)(ULONG_PTR)&known_window;
        native_window_set(&known_window,expected_x,expected_y,expected_w,expected_h);
        st=owner_state_for(expected_owner,1); strcpy(st->class_name,"UITransBalloonText");
        box_primitive.verts=&box_quad; box_primitive.count=4;
        left_primitive.verts=&text_left; left_primitive.count=4;
        right_primitive.verts=&text_right; right_primitive.count=4;
        quad(&box_quad,expected_x,expected_y,146,106);
        quad(&text_left,expected_x,expected_y,73,106);
        quad(&text_right,expected_x+73,expected_y,73,106);
        CHECK(owner_background_draw_c(expected_owner,expected_x,expected_y,146,106,expected_color)==background_return);
        CHECK(owner_bitmap_draw_c(expected_owner,(void*)(ULONG_PTR)0x3456,(void*)native_bitmap,
                                  expected_x,expected_y,146,106,expected_color)==bitmap_return);
        CHECK(scaled(&box_quad,&box)==&box && scaled(&text_left,&left)==&left && scaled(&text_right,&right)==&right);
        expected_left=3440.0f+(3246.0f-3440.0f)*scale;
        expected_right=3440.0f+(3392.0f-3440.0f)*scale;
        expected_top=(171.0f+35.0f*entry)*scale;
        transformed(&box_quad,&box,3440,0,scale,0,0);
        transformed(&text_left,&left,3440,0,scale,0,0);
        transformed(&text_right,&right,3440,0,scale,0,0);
        CHECK(fabsf(box.f[0][0]-expected_left)<0.001f && fabsf(box.f[0][1]-expected_top)<0.001f);
        CHECK(fabsf((expected_right-expected_left)-146.0f*scale)<0.001f);
        CHECK(!g_owner_bitmap_active_count && !st->last_input_order);
        /* Reenter after absence; no fallback-group warmup is available. */
        g_ui_present_serial+=10;
        CHECK(owner_bitmap_prepare(expected_owner,expected_x,expected_y,146,106));
        CHECK(g_owner_bitmap_scope.fit_scale==scale && !g_owner_bitmap_scope.native_size);
        /* The shared RTTI on an unrelated speech object still uses its live
           world bottom-center, even while the buff popup is active. */
        st=owner_state_for((DWORD)(ULONG_PTR)&second_window,1); strcpy(st->class_name,"UITransBalloonText");
        CHECK(owner_bitmap_prepare(st->object_ptr,700,500,146,106));
        CHECK(g_owner_bitmap_scope.ax==773 && g_owner_bitmap_scope.ay==606);
        CHECK(g_owner_bitmap_scope.offset_x==0 && g_owner_bitmap_scope.offset_y==0);
    }
}
static void oversized_and_live_scale(void) {
    OwnerWindowState* st; Quad original,out; DWORD i;
    reset_all(); attach_buff(); g_ui_screen_w=1920; g_ui_screen_h=1080;
    st=owner_state_for((DWORD)(ULONG_PTR)&known_window,1); strcpy(st->class_name,"UITransBalloonText");
    g_ui_scale_percent=150; CHECK(owner_bitmap_prepare(st->object_ptr,1500,171,200,100));
    CHECK(g_owner_bitmap_scope.fit_scale==1.5f);
    g_ui_scale_percent=200; CHECK(owner_bitmap_prepare(st->object_ptr,1500,171,200,100));
    CHECK(g_owner_bitmap_scope.fit_scale==2.0f);
    CHECK(owner_bitmap_prepare(st->object_ptr,400,171,1200,1000));
    CHECK(!g_owner_bitmap_scope.native_size && g_owner_bitmap_scope.fit_scale<2.0f);
    quad(&original,400,171,1200,1000);
    owner_bitmap_note_vertices(&original,4,&g_owner_bitmap_scope);
    CHECK(scaled(&original,&out)==&out);
    for(i=0;i<4;++i) CHECK(out.f[i][0]>=-0.01f && out.f[i][0]<=1920.01f &&
                            out.f[i][1]>=-0.01f && out.f[i][1]<=1080.01f);
}
int main(void) {
    CHECK(sizeof(void*)==4);
    background_baseline(); exact_identity(); buff_box_and_text(); oversized_and_live_scale();
    puts("PASS buff: native thiscall/return forwarding, live scene+5E8 and vtable identity, unreadable/reused rejection, first/reentry 150/200% queued box/text attachment, and unchanged actor speech");
    return 0;
}
'''
def main():
    with tempfile.TemporaryDirectory(prefix='prm-buff-test-') as directory:
        c=Path(directory)/'buff.c'; binary=Path(directory)/'buff'
        c.write_text(prefix+bitmap.types+stubs+background.production+helpers+tests)
        subprocess.run([os.environ.get('CC','clang'),'-m32','-std=c11','-O1','-g','-Wall','-Wextra',
                        '-Wno-unused-variable','-Wno-unused-parameter','-Wno-unused-function',
                        '-fsanitize=address,undefined','-fno-omit-frame-pointer',str(c),'-o',str(binary)],check=True)
        subprocess.run([str(binary)],check=True)
if __name__=='__main__': main()
