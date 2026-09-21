#!/usr/bin/env python3
"""i386 ASan/UBSan checks for buff triangles, drag ACT, and combat draw scopes."""
from pathlib import Path
import os
import subprocess
import tempfile
import test_background as bg
import test_bitmap as bm

prefix = bg.prefix.replace('n<=128', 'n<=4096') + r'''
typedef DWORD (__attribute__((thiscall)) *PFN_WindowOverlayDraw)(void*);
typedef void (__attribute__((thiscall)) *PFN_CursorDraw)(void*,LONG,LONG,void*,void*,DWORD,DWORD,float,float,DWORD,DWORD);
typedef DWORD (__attribute__((thiscall)) *PFN_CombatDraw)(void*,void*,DWORD);
static PFN_WindowOverlayDraw g_owner_buff_draw;
static PFN_CursorDraw g_owner_drag_sprite;
static PFN_CombatDraw g_owner_combat_draw;
static DWORD g_owner_buff_icons,g_owner_drag_icons,g_owner_combat_sprites;
static POINT raw_point;
static int raw_available=1;
static int g_owner_input_remap_enabled=1;
static int input_read_raw_point(POINT* out,RECT* rect) {
    if(!raw_available) return 0; *out=raw_point; return 1;
}
'''
constants = '\n'.join(bm.constant(n) for n in ('PRM_NUM_EFFECT_VTABLE_RVA','PRM_MSG_EFFECT_VTABLE_RVA'))
production = '\n'.join(bm.function(n) for n in (
    'owner_effect_ui_active','owner_buff_anchor','owner_buff_hover_point','owner_buff_draw_scoped',
    'owner_drag_sprite_scoped','owner_is_combat_text','owner_combat_draw_scoped'))
tests = bg.tests.replace('int main(void)', 'int background_baseline(void)') + r'''
static union { DWORD align; BYTE bytes[1024]; } effect;
static float triangle[3][8];
static DWORD buff_calls,drag_calls,combat_calls;
static LONG drag_x,drag_y;
static float drag_scale,combat_scale;
static DWORD __attribute__((thiscall)) buff_draw(void* self) {
    struct { void* verts; DWORD n; } primitive={triangle,3};
    CHECK(self==effect.bytes); ++buff_calls;
    /* Queue delayed vertices exactly as native 4A0890 -> 4A0550 does. */
    g_owner_bitmap_submit=0;
    owner_bitmap_queue_scoped((void*)0x1234,&primitive,0x201);
    return 0xabc123;
}
static void __attribute__((thiscall)) drag_draw(void* self,LONG x,LONG y,void* act,void* spr,
    DWORD action,DWORD frame,float scale,float rotation,DWORD color,DWORD flags) {
    CHECK(self==effect.bytes && act==(void*)0x1234 && spr==(void*)0x5678);
    CHECK(action==2 && frame==3 && rotation==0.25f && color==0xfaffffff && flags==0x201);
    CHECK(!g_owner_bitmap_scope.object_ptr);
    CHECK(x==drag_x && y==drag_y && scale==drag_scale); ++drag_calls;
}
static DWORD __attribute__((thiscall)) combat_draw(void* self,void* view,DWORD flags) {
    CHECK(self==effect.bytes && view==(void*)0x1234 && flags==0x42);
    CHECK(*(float*)(effect.bytes+0x50)==combat_scale);
    CHECK(*(float*)(effect.bytes+0x10)==123.5f && *(float*)(effect.bytes+0x14)==-42.0f);
    ++combat_calls; return 0xc0ffee;
}
static void buff_triangles(void) {
    DWORD i,j; BYTE scratch[96]; const void* out; OwnerBitmapScope saved;
    reset_all(); memset(&effect,0,sizeof(effect)); memset(triangle,0,sizeof(triangle));
    *(DWORD*)effect.bytes=0x9876; effect.bytes[0x3e0]=0x62;
    *(DWORD*)(effect.bytes+0x1bc)=0x201; *(DWORD*)(effect.bytes+0x1d4)=4;
    g_owner_buff_draw=buff_draw; g_ui_screen_w=3440; g_ui_screen_h=1440; g_ui_scale_percent=200;
    g_owner_bitmap_scope.object_ptr=0x777; g_owner_bitmap_scope.thread=17; saved=g_owner_bitmap_scope;
    for(i=0;i<3;++i) {
        triangle[i][0]=3392.0f+(float)(i&1)*32.0f; triangle[i][1]=169.0f+(float)(i>>1)*32.0f;
        triangle[i][2]=0.000001f; triangle[i][3]=1.0f;
    }
    CHECK(owner_buff_draw_scoped(effect.bytes)==0xabc123);
    CHECK(!memcmp(&saved,&g_owner_bitmap_scope,sizeof(saved)));
    out=make_scaled_ui_vertices(4,0x1c4,triangle,3,scratch,sizeof(scratch),0,0);
    CHECK(out==scratch);
    for(i=0;i<3;++i) {
        const float* v=(const float*)(scratch+i*32);
        CHECK(v[0]==3440+(triangle[i][0]-3440)*2 && v[1]==triangle[i][1]*2);
        CHECK(!memcmp(v+2,triangle[i]+2,24));
    }
    CHECK(!g_owner_bitmap_active_count);
    /* Shared renderer: non-buff flash, wrong flags, disabled state, and wrong
       thread must clear parent ownership, including reused vertex memory. */
    for(j=0;j<4;++j) {
        effect.bytes[0x3e0]=0x62; *(DWORD*)(effect.bytes+0x1bc)=0x201;
        g_ui_runtime_enabled=1; g_GetCurrentThreadId=thread_id;
        if(j==0) effect.bytes[0x3e0]=0;
        if(j==1) *(DWORD*)(effect.bytes+0x1bc)=1;
        if(j==2) g_ui_runtime_enabled=0;
        if(j==3) g_GetCurrentThreadId=0;
        CHECK(owner_buff_draw_scoped(effect.bytes)==0xabc123);
        CHECK(make_scaled_ui_vertices(4,0x1c4,triangle,3,scratch,sizeof(scratch),0,0)==triangle);
        CHECK(!memcmp(&saved,&g_owner_bitmap_scope,sizeof(saved)));
    }
    g_GetCurrentThreadId=thread_id; g_ui_runtime_enabled=1;
    /* Fingerprint all three vertices; exactly 96 readable bytes under ASan. */
    for(i=0;i<3;++i) for(j=0;j<8;++j) if(j!=4 && j!=5) {
        float ax,ay; owner_buff_draw_scoped(effect.bytes);
        ((DWORD*)triangle[i])[j]^=1;
        CHECK(!owner_bitmap_consume_vertices(0x1c4,triangle,3,&ax,&ay));
        ((DWORD*)triangle[i])[j]^=1;
    }
}
static void buff_preferences(void) {
    BYTE scratch[96]; const float* out; LONG x=0,y=0;
    reset_all();memset(&effect,0,sizeof(effect));
    effect.bytes[0x3e0]=0x62;*(DWORD*)(effect.bytes+0x1bc)=0x201;*(DWORD*)(effect.bytes+0x1d4)=4;
    g_ui_screen_w=3440;g_ui_screen_h=1440;g_ui_scale_percent=100;
    g_owner_buff_draw=buff_draw;g_GetCurrentThreadId=thread_id;
    g_input_enabled=g_input_runtime_enabled=1;
    CHECK(ui_window_set("BuffIcons",300,25,-10));
    owner_buff_draw_scoped(effect.bytes);
    out=make_scaled_ui_vertices(4,0x1c4,triangle,3,scratch,sizeof(scratch),0,0);
    CHECK((const void*)out==scratch);
    CHECK(out[0]==3440+(triangle[0][0]-3440)*3+25);
    CHECK(out[1]==triangle[0][1]*3-10);
    raw_point.x=3440+(3392-3440)*3+25;raw_point.y=169*3-10;
    owner_buff_hover_point(&x,&y);CHECK(x==3392 && y==169);
    CHECK(ui_window_set("BuffIcons",0,0,0));
    puts("PASS buff preferences: independent 300% visuals, position offsets and matching native hover coordinates with 100% global default");
}
static void dragged_sprite(void) {
    int percent,enabled; OwnerBitmapScope saved;
    reset_all(); g_owner_drag_sprite=drag_draw;
    g_owner_bitmap_scope.object_ptr=0x777; saved=g_owner_bitmap_scope;
    raw_point.x=1700; raw_point.y=800;
    for(percent=100;percent<=250;percent+=25) for(enabled=0;enabled<=1;++enabled) {
        g_ui_runtime_enabled=enabled; g_ui_scale_percent=percent;
        drag_x=enabled?1700:123; drag_y=enabled?800:456;
        drag_scale=enabled?0.5f*(float)percent/100.0f:0.5f;
        owner_drag_sprite_scoped(effect.bytes,123,456,(void*)0x1234,(void*)0x5678,2,3,0.5f,0.25f,0xfaffffff,0x201);
        CHECK(!memcmp(&saved,&g_owner_bitmap_scope,sizeof(saved)));
    }
    raw_available=0; drag_x=123;drag_y=456;drag_scale=0.5f;
    owner_drag_sprite_scoped(effect.bytes,123,456,(void*)0x1234,(void*)0x5678,2,3,0.5f,0.25f,0xfaffffff,0x201);
    raw_available=1;
}
static void combat_sprites(void) {
    DWORD kind,vt; int enabled;
    reset_all(); g_owner_combat_draw=combat_draw; g_ui_scale_percent=200;
    *(float*)(effect.bytes+0x10)=123.5f; *(float*)(effect.bytes+0x14)=-42.0f;
    for(vt=0;vt<3;++vt) for(kind=0;kind<120;++kind) for(enabled=0;enabled<=1;++enabled) {
        int accepted=vt==1 || (vt==2 && (kind==14 || kind==16 || kind==21 || kind==22 || kind==114));
        *(DWORD*)effect.bytes=(DWORD)(ULONG_PTR)g_exe+(vt==1?PRM_NUM_EFFECT_VTABLE_RVA:vt==2?PRM_MSG_EFFECT_VTABLE_RVA:0x1234);
        *(DWORD*)(effect.bytes+0x1a0)=kind; *(float*)(effect.bytes+0x50)=1.25f;
        g_ui_runtime_enabled=enabled; combat_scale=enabled && accepted?2.5f:1.25f;
        CHECK(owner_combat_draw_scoped(effect.bytes,(void*)0x1234,0x42)==0xc0ffee);
        CHECK(*(float*)(effect.bytes+0x50)==1.25f);
    }
}
int main(void) {
    CHECK(sizeof(void*)==4); background_baseline(); buff_triangles(); buff_preferences(); dragged_sprite(); combat_sprites();
    CHECK(buff_calls && drag_calls && combat_calls);
    puts("PASS effect sprites: three-vertex delayed ownership/fingerprints, world exclusion, nested scopes, drag mouse/scale/ABI, numeric effect allowlist and animation-state restoration");
    return 0;
}
'''
def main():
    with tempfile.TemporaryDirectory(prefix='prm-effect-test-') as d:
        c=Path(d)/'effects.c'; binary=Path(d)/'effects'
        c.write_text(prefix+constants+"\n"+bm.types+bg.stubs+bg.production+production+tests)
        subprocess.run([os.environ.get('CC','clang'),'-m32','-std=c11','-O1','-g','-Wall','-Wextra',
            '-Wno-unused-variable','-Wno-unused-parameter','-Wno-unused-function',
            '-fsanitize=address,undefined','-fno-omit-frame-pointer',str(c),'-o',str(binary)],check=True)
        subprocess.run([str(binary)],check=True)
if __name__=='__main__':main()
