#!/usr/bin/env python3
"""Exercise actual map scope, queue ABI, registry, and final scaler in 32 bits.

Native object lookup and renderer calls use fixtures. The real map wrappers,
scope preparation, provenance registry, and vertex scaler are source-extracted.
The 32-bit host build preserves the native primitive pointer/count layout and
thiscall ABI; ASan/UBSan check the composed render path.
"""

from pathlib import Path
import os
import subprocess
import tempfile

import test_bitmap as bitmap


prefix = bitmap.prefix.replace(
    "static DWORD thread_id(void) { return 17; }",
    "static DWORD current_thread=17;\nstatic DWORD thread_id(void) { return current_thread; }",
).replace(
    "typedef DWORD (*PFN_BitmapDraw)",
    "typedef DWORD (__attribute__((thiscall)) *PFN_BitmapDraw)",
).replace("#define WINAPI\n", "#define WINAPI __attribute__((stdcall))\n")
prefix += r"""
typedef DWORD (__attribute__((thiscall)) *PFN_WindowOverlayDraw)(void*);
typedef void (__attribute__((thiscall)) *PFN_SpriteSubmit)(void*,void*,DWORD);
static PFN_WindowOverlayDraw g_owner_map_draw;
static PFN_SpriteSubmit g_owner_bitmap_submit;
typedef struct { DWORD words[12]; } NativeWindow;
static NativeWindow map_window,unknown_window;
"""

stubs = bitmap.stubs.replace(
    "static OwnerWindowState* owner_state_for(",
    "static OwnerWindowState* fixture_state_for(",
)
stubs += r"""
static OwnerWindowState* owner_state_for(DWORD obj,int create) {
    OwnerWindowState* st;
    if(obj==(DWORD)(ULONG_PTR)&map_window) {
        st=fixture_state_for(1,create);
        if(st && create) {
            st->object_ptr=obj;
            st->vtable_ptr=*(DWORD*)(&map_window);
        }
        return st;
    }
    return fixture_state_for(obj,create);
}
"""

production = bitmap.production + "\n" + "\n".join(bitmap.function(name) for name in (
    "owner_bitmap_window_draw", "owner_map_note_occlusion", "owner_map_draw_scoped", "owner_bitmap_queue_scoped",
))
helpers = bitmap.tests[:bitmap.tests.index("static void split_tiles(void)")]

tests = r"""
/* Native primitive layout is pointer at +0 and count at +4. */
typedef struct { void* verts; DWORD count; } Primitive;
static Quad map_quads[5];
static Primitive primitives[5];
static DWORD queue_calls,map_calls,expected_map_native;
static DWORD name_bitmap_calls;
static void* expected_renderer;
static Primitive* expected_primitive;
static DWORD expected_flags;
static OwnerBitmapScope observed_map_scope;
static void __attribute__((thiscall)) native_queue(void* renderer,void* primitive,DWORD flags) {
    DWORD j;
    CHECK(renderer==expected_renderer && primitive==expected_primitive && flags==expected_flags);
    ++queue_calls;
    /* The real native queue may update specular without changing provenance. */
    if(primitive && primitive!=unreadable) {
        Primitive* p=primitive;
        if(p->count==4) for(j=0;j<4;++j) ((Quad*)p->verts)->d[j][5]=0xff345678;
    }
}
static void submit(unsigned int index,DWORD flags) {
    expected_renderer=(void*)(ULONG_PTR)0x1234;
    expected_primitive=&primitives[index]; expected_flags=flags;
    owner_bitmap_queue_scoped(expected_renderer,expected_primitive,flags);
}
static DWORD __attribute__((thiscall)) native_map(void* self) {
    unsigned int i;
    CHECK(self==&map_window);
    CHECK(g_owner_bitmap_scope.object_ptr==(DWORD)(ULONG_PTR)&map_window);
    CHECK(g_owner_bitmap_scope.thread==17 && g_owner_bitmap_scope.native_size==(int)expected_map_native);
    observed_map_scope=g_owner_bitmap_scope;
    for(i=0;i<4;++i) submit(i,0x201);
    ++map_calls;
    return 0xcafef00d;
}
static DWORD __attribute__((thiscall)) native_bitmap(void* dc,LONG x,LONG y,LONG w,LONG h,DWORD color) {
    CHECK(dc==(void*)(ULONG_PTR)0x3456 && x==0 && y==0 && w==1920 && h==1080 && color==0xff123456);
    CHECK(g_owner_bitmap_scope.object_ptr==observed_map_scope.object_ptr);
    CHECK(g_owner_bitmap_scope.ax==observed_map_scope.ax && g_owner_bitmap_scope.ay==observed_map_scope.ay);
    CHECK(g_owner_bitmap_scope.native_size==observed_map_scope.native_size);
    submit(4,0x201);
    return 0x89abcdef;
}
static DWORD __attribute__((thiscall)) native_name_bitmap(void* dc,LONG x,LONG y,LONG w,LONG h,DWORD color) {
    CHECK(dc==(void*)(ULONG_PTR)0x4567 && color==0xffabcdef);
    CHECK(g_owner_bitmap_scope.object_ptr!=0 && g_owner_bitmap_scope.thread==current_thread);
    ++name_bitmap_calls;
    return 0x13572468;
}
static void map_reset(void) {
    DWORD i,j; OwnerWindowState* map_state;
    reset(); current_thread=17;
    memset(&map_window,0,sizeof(map_window)); memset(&unknown_window,0,sizeof(unknown_window));
    map_window.words[0x14/4]=1920; map_window.words[0x18/4]=1080;
    map_window.words[0x28/4]=1;
    unknown_window.words[0x14/4]=100; unknown_window.words[0x18/4]=100;
    if(!g_exe) { g_exe=calloc(1,0xab8000UL); CHECK(g_exe); g_exe_size=0xab8000UL; }
    memset((BYTE*)g_exe+0xab76d8UL+0x3c4,0,4);
    *(DWORD*)((BYTE*)g_exe+0xab76d8UL+0x3c4)=(DWORD)(ULONG_PTR)&map_window;
    map_window.words[0]=(DWORD)(ULONG_PTR)((BYTE*)g_exe+PRM_MAP_VTABLE_RVA);
    map_state=owner_state_for((DWORD)(ULONG_PTR)&map_window,1);
    CHECK(map_state); strcpy(map_state->class_name,"UIRoMapWnd");
    queue_calls=map_calls=name_bitmap_calls=0; g_owner_map_draws=0;
    g_owner_map_draw=native_map; g_owner_bitmap_submit=native_queue;
    /* Four direct overlays occupy different areas of the full-screen map. */
    quad(&map_quads[0],110,90,210,130);  /* hovered region shading */
    quad(&map_quads[1],320,110,130,130); /* texture preview */
    quad(&map_quads[2],1210,640,80,35); /* route arrow/link */
    quad(&map_quads[3],810,590,24,40);  /* animated map marker */
    quad(&map_quads[4],0,0,256,256);   /* cached full-map bitmap tile */
    for(i=0;i<5;++i) {
        primitives[i].verts=&map_quads[i]; primitives[i].count=4;
        if(i==0 || i==2 || i==3) for(j=0;j<4;++j) {
            map_quads[i].f[j][2]=0.8f; map_quads[i].f[j][3]=1.0f;
        }
    }
}
static void shared_map_transform(void) {
    unsigned int global,i; Quad before,out; OwnerBitmapScope outer;
    UIRectF region={110,90,320,220}; float region_ax,region_ay;
    for(global=0;global<2;++global) {
        map_reset(); g_ui_scale_global=global; expected_map_native=!global;
        CHECK(owner_bitmap_prepare(2,1700,20,100,100)); outer=g_owner_bitmap_scope;
        CHECK(owner_map_draw_scoped(&map_window)==0xcafef00d);
        CHECK(map_calls==1 && g_owner_map_draws==1 && queue_calls==4);
        CHECK(!memcmp(&g_owner_bitmap_scope,&outer,sizeof(outer)));
        CHECK(owner_bitmap_draw_c((DWORD)(ULONG_PTR)&map_window,(void*)(ULONG_PTR)0x3456,
              (void*)native_bitmap,0,0,1920,1080,0xff123456)==0x89abcdef);
        CHECK(queue_calls==5 && g_owner_bitmap_active_count==5);
        CHECK(!memcmp(&g_owner_bitmap_scope,&outer,sizeof(outer)));
        CHECK(observed_map_scope.ax==960 && observed_map_scope.ay==540);
        choose_group_anchor(&region,&region_ax,&region_ay);
        CHECK(region_ax!=observed_map_scope.ax || region_ay!=observed_map_scope.ay);
        for(i=0;i<5;++i) {
            before=map_quads[i];
            if(global) {
                CHECK(scale(&map_quads[i],&out,0)==&out);
                transformed(&map_quads[i],&out,observed_map_scope.ax,observed_map_scope.ay);
            } else CHECK(scale(&map_quads[i],&out,0)==&map_quads[i]);
            CHECK(!memcmp(&before,&map_quads[i],sizeof(before)));
        }
        CHECK(g_owner_bitmap_matched==5 && !g_owner_bitmap_active_count);
        CHECK(g_ui_scaled_draws==(global?5:0));
        CHECK(!fallback_collected && !legacy_matches && !g_owner_bitmap_mismatched);
    }
}
static void map_occludes_world_name_bitmaps(void) {
    const char* classes[]={"UINameBalloonText","UIVerticalNameBalloonText"};
    DWORD i; OwnerWindowState* st;
    for(i=0;i<2;++i) {
        map_reset();
        st=owner_state_for(3,1); CHECK(st); strcpy(st->class_name,classes[i]);
        /* A name rendered before the map remains available underneath it. */
        CHECK(owner_bitmap_draw_c(3,(void*)(ULONG_PTR)0x4567,(void*)native_name_bitmap,
              600,300,120,24,0xffabcdef)==0x13572468);
        CHECK(name_bitmap_calls==1 && !g_owner_map_occlusion.valid);
        CHECK(owner_map_draw_scoped(&map_window)==0xcafef00d);
        CHECK(g_owner_map_occlusion.valid && g_owner_map_occlusion.present==g_ui_present_serial+1);
        /* The same exact class rendered after the actual fullscreen map draw
           is suppressed before its original cached-bitmap callback. */
        CHECK(owner_bitmap_draw_c(3,(void*)(ULONG_PTR)0x4567,(void*)native_name_bitmap,
              600,300,120,24,0xffabcdef)==0);
        CHECK(name_bitmap_calls==1 && g_owner_map_name_suppressed==1);
    }

    /* Closing/visibility changes, a present boundary, or object reuse all
       revoke the marker before an unrelated name draw can consume it. */
    map_reset(); st=owner_state_for(3,1); strcpy(st->class_name,classes[0]);
    CHECK(owner_map_draw_scoped(&map_window)==0xcafef00d);
    map_window.words[0x28/4]=0;
    CHECK(owner_bitmap_draw_c(3,(void*)(ULONG_PTR)0x4567,(void*)native_name_bitmap,
          600,300,120,24,0xffabcdef)==0x13572468);
    CHECK(name_bitmap_calls==1);

    map_reset(); st=owner_state_for(3,1); strcpy(st->class_name,classes[0]);
    CHECK(owner_map_draw_scoped(&map_window)==0xcafef00d);
    ++g_ui_present_serial;
    CHECK(owner_bitmap_draw_c(3,(void*)(ULONG_PTR)0x4567,(void*)native_name_bitmap,
          600,300,120,24,0xffabcdef)==0x13572468);
    CHECK(name_bitmap_calls==1);

    map_reset(); st=owner_state_for(3,1); strcpy(st->class_name,classes[0]);
    CHECK(owner_map_draw_scoped(&map_window)==0xcafef00d);
    map_window.words[0] ^= 4; /* same allocation, no longer the map vtable */
    CHECK(owner_bitmap_draw_c(3,(void*)(ULONG_PTR)0x4567,(void*)native_name_bitmap,
          600,300,120,24,0xffabcdef)==0x13572468);
    CHECK(name_bitmap_calls==1);

    /* Same-frame thread, geometry, singleton and runtime changes cannot
       reuse an earlier fullscreen marker. */
    for(i=0;i<5;++i) {
        map_reset(); st=owner_state_for(3,1); strcpy(st->class_name,classes[0]);
        CHECK(owner_map_draw_scoped(&map_window)==0xcafef00d);
        if(i==0) current_thread=18;
        if(i==1) map_window.words[0x14/4]=1024;
        if(i==2) {
            map_window.words[0x1c/4]=(DWORD)-1;
            map_window.words[0x14/4]=1921; /* still fullscreen, but changed */
        }
        if(i==3) *(DWORD*)((BYTE*)g_exe+0xab76d8UL+0x3c4)=0;
        if(i==4) g_ui_runtime_enabled=0;
        CHECK(owner_bitmap_draw_c(3,(void*)(ULONG_PTR)0x4567,(void*)native_name_bitmap,
              600,300,120,24,0xffabcdef)==0x13572468);
        CHECK(name_bitmap_calls==1 && !g_owner_map_name_suppressed);
    }

    /* A different fullscreen UIWindow does not become a world-name
       occluder. Scaling disabled also leaves the original render path alone. */
    map_reset(); st=owner_state_for(2,1); strcpy(st->class_name,"UIItemWnd");
    CHECK(owner_bitmap_draw_c(2,(void*)(ULONG_PTR)0x4567,(void*)native_name_bitmap,
          0,0,1920,1080,0xffabcdef)==0x13572468);
    CHECK(name_bitmap_calls==1 && !g_owner_map_name_suppressed);
    map_reset(); g_ui_runtime_enabled=0; st=owner_state_for(3,1); strcpy(st->class_name,classes[0]);
    CHECK(owner_map_draw_scoped(&map_window)==0xcafef00d);
    CHECK(!g_owner_map_occlusion.valid);
    CHECK(owner_bitmap_draw_c(3,(void*)(ULONG_PTR)0x4567,(void*)native_name_bitmap,
          600,300,120,24,0xffabcdef)==0x13572468);
    CHECK(name_bitmap_calls==1);
    map_reset(); g_owner_map_draw=0; st=owner_state_for(3,1); strcpy(st->class_name,classes[0]);
    CHECK(owner_map_draw_scoped(&map_window)==0);
    CHECK(!g_owner_map_occlusion.valid);
    CHECK(owner_bitmap_draw_c(3,(void*)(ULONG_PTR)0x4567,(void*)native_name_bitmap,
          600,300,120,24,0xffabcdef)==0x13572468);
    CHECK(name_bitmap_calls==1);
}
static DWORD __attribute__((thiscall)) native_unowned(void* self) {
    CHECK(self==&unknown_window);
    CHECK(!g_owner_bitmap_scope.object_ptr && !g_owner_bitmap_scope.thread);
    submit(0,0xabc201); ++map_calls; return 0xfeedbaad;
}
static void scope_and_queue_isolation(void) {
    OwnerBitmapScope outer; float ax=0,ay=0; DWORD before;
    map_reset(); expected_map_native=0;
    CHECK(owner_bitmap_prepare((DWORD)(ULONG_PTR)&map_window,0,0,1920,1080));
    outer=g_owner_bitmap_scope;
    submit(0,0x201); CHECK(g_owner_bitmap_active_count==1);
    /* Reuse at the same queue on another thread must revoke the previous tag. */
    current_thread=18; before=queue_calls; submit(0,0x800201);
    CHECK(queue_calls==before+1 && !g_owner_bitmap_active_count);
    CHECK(!consume(&map_quads[0],&ax,&ay));
    CHECK(!memcmp(&g_owner_bitmap_scope,&outer,sizeof(outer)));
    current_thread=17; submit(0,0x201); CHECK(g_owner_bitmap_active_count==1);
    g_GetCurrentThreadId=0; submit(0,0x777); CHECK(!g_owner_bitmap_active_count);
    g_GetCurrentThreadId=thread_id;
    /* Unknown nested windows cannot borrow a surrounding map's scope. */
    before=queue_calls;
    CHECK(owner_bitmap_window_draw(&unknown_window,native_unowned)==0xfeedbaad);
    CHECK(queue_calls==before+1 && !g_owner_bitmap_active_count);
    CHECK(!memcmp(&g_owner_bitmap_scope,&outer,sizeof(outer)));
    CHECK(!consume(&map_quads[0],&ax,&ay));
    /* An unreadable native window still forwards and restores the parent. */
    unreadable=(BYTE*)&unknown_window+0x14;
    CHECK(owner_bitmap_window_draw(&unknown_window,native_unowned)==0xfeedbaad);
    CHECK(!memcmp(&g_owner_bitmap_scope,&outer,sizeof(outer)));
    unreadable=0;
    /* Null/unreadable primitive forwarding must not dereference native input. */
    expected_renderer=(void*)(ULONG_PTR)0x1234; expected_primitive=0; expected_flags=0x778;
    before=queue_calls; owner_bitmap_queue_scoped(expected_renderer,0,expected_flags);
    CHECK(queue_calls==before+1);
    unreadable=&primitives[0]; expected_primitive=&primitives[0];
    owner_bitmap_queue_scoped(expected_renderer,expected_primitive,expected_flags);
    CHECK(queue_calls==before+2 && !g_owner_bitmap_active_count); unreadable=0;
    /* No original callback is a harmless scoped no-op. */
    g_owner_map_draw=0;
    CHECK(owner_map_draw_scoped(&map_window)==0);
    CHECK(!memcmp(&g_owner_bitmap_scope,&outer,sizeof(outer)));
}
static void disabled_map_render(void) {
    unsigned int setting,i; Quad out;
    for(setting=0;setting<2;++setting) {
        map_reset(); expected_map_native=0;
        CHECK(owner_map_draw_scoped(&map_window)==0xcafef00d);
        if(setting) g_ui_enabled=0; else g_ui_runtime_enabled=0;
        for(i=0;i<4;++i) CHECK(scale(&map_quads[i],&out,0)==&map_quads[i]);
        CHECK(g_owner_bitmap_matched==4 && !g_owner_bitmap_active_count);
        CHECK(!g_ui_scaled_draws && !fallback_collected);
    }
}
int main(void) {
    CHECK(sizeof(void*)==4 && sizeof(Primitive)==8);
    shared_map_transform(); map_occludes_world_name_bitmaps(); scope_and_queue_isolation(); disabled_map_render();
    puts("PASS map ownership: real 32-bit wrapper/queue ABI, shared bitmap/region/preview/route/marker transform, fullscreen map draw-order occlusion for both world-name classes, immediate close/present/reuse/runtime-disable/no-original isolation, native-size policy, depth/RHW provenance, original vertices preserved, scope restoration, argument forwarding, wrong-thread and unowned isolation, disabled scaling");
    return 0;
}
"""


def main():
    with tempfile.TemporaryDirectory(prefix="prm-map-test-") as directory:
        c_file = Path(directory) / "map_test.c"
        binary = Path(directory) / "map_test"
        c_file.write_text(prefix + bitmap.types + stubs + production + helpers + tests)
        subprocess.run([
            os.environ.get("CC", "clang"), "-m32", "-std=c11", "-O1", "-g",
            "-Wall", "-Wextra", "-Wno-unused-variable", "-Wno-unused-parameter",
            "-Wno-unused-function", "-fsanitize=address,undefined",
            "-fno-omit-frame-pointer", str(c_file), "-o", str(binary),
        ], check=True)
        subprocess.run([str(binary)], check=True)


if __name__ == "__main__":
    main()
