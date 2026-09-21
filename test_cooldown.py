"""Production cooldown builder ownership: hotbar transform vs buff anchor."""
from pathlib import Path
import tempfile,subprocess
import test_bitmap as bm
import test_background as bg
prefix=bg.prefix.replace('n<=128','n<=4096')+'''
typedef DWORD (__attribute__((thiscall)) *PFN_CooldownBuild)(void*,LONG,LONG,LONG,LONG,void*,DWORD,LONG,LONG);
static PFN_CooldownBuild g_owner_cooldown_build;
'''
prefix+='static void cooldown_diagnostic(void* w,const void* s,const void* p,int r) {}\n'
prod='\n'.join(bm.function(n) for n in ('owner_effect_ui_active','owner_cooldown_build_c'))
tests=bg.tests.replace('int main(void)','int background_baseline(void)')+r'''
static union { DWORD align; BYTE bytes[0x338]; } mesh[2];
static DWORD __attribute__((thiscall)) build(void* self,LONG x,LONG y,LONG hw,LONG hh,void* data,DWORD mode,LONG dx,LONG dy) {
    float* v=(float*)((BYTE*)data+0x28); DWORD i;
    CHECK(self==(void*)123 && x==1 && y==2 && hw==12 && hh==12 && mode==4 && dx==5 && dy==6);
    for(i=0;i<24;++i) {v[i*8]=600+(i%3)*8;v[i*8+1]=400+(i%4)*8;v[i*8+2]=0;v[i*8+3]=1;}
    return 0xabcdef;
}
static void cooldown_case(int percent,LONG wx,LONG wy) {
    DWORD i; BYTE scratch[768]; const float* out; OwnerWindowState* st;
    OwnerBitmapScope saved; float ax,ay,scale,dx,dy;
    reset_all();g_owner_cooldown_build=build;g_ui_scale_percent=percent;
    native_window_set(&known_window,wx,wy,290,132);
    st=owner_state_for((DWORD)(ULONG_PTR)&known_window,1);
    strcpy(st->class_name,"UIShortCutWnd");
    for(i=0;i<2;++i) {
        *(DWORD*)(mesh[i].bytes+0xc)=24;
        *(LONG*)(mesh[i].bytes+0x328)=600;*(LONG*)(mesh[i].bytes+0x32c)=400;
        *(DWORD*)(mesh[i].bytes+0x334)=0xaa000000;
    }
    st->offset_x=17; st->offset_y=-11;
    CHECK(owner_bitmap_prepare((DWORD)(ULONG_PTR)&known_window,wx,wy,290,132));
    ax=g_owner_bitmap_scope.ax;ay=g_owner_bitmap_scope.ay;scale=g_owner_bitmap_scope.fit_scale;
    dx=g_owner_bitmap_scope.offset_x;dy=g_owner_bitmap_scope.offset_y;
    /* Deliberately leave an unrelated buff scope active: hotbar must override it. */
    g_owner_bitmap_scope.ax=3440;g_owner_bitmap_scope.ay=0;g_owner_bitmap_scope.fit_scale=2;
    saved=g_owner_bitmap_scope;
    CHECK(owner_cooldown_build_c((void*)123,&known_window,1,2,12,12,mesh[0].bytes,4,5,6)==0xabcdef);
    CHECK(!memcmp(&saved,&g_owner_bitmap_scope,sizeof(saved)));
    CHECK(owner_cooldown_build_c((void*)123,0,1,2,12,12,mesh[1].bytes,4,5,6)==0xabcdef);
    memset(&g_owner_bitmap_scope,0,sizeof(g_owner_bitmap_scope));
    out=make_scaled_ui_vertices(4,0x1c4,mesh[1].bytes+0x28,24,scratch,sizeof(scratch),0,0);
    CHECK((const void*)out==scratch && out[0]==3440+(600-3440)*2+saved.offset_x);
    out=make_scaled_ui_vertices(4,0x1c4,mesh[0].bytes+0x28,24,scratch,sizeof(scratch),0,0);
    CHECK((const void*)out==scratch);
    for(i=0;i<24;++i) {
        const float* v=(const float*)(mesh[0].bytes+0x28+i*32);
        CHECK(out[i*8]==ax+(v[0]-ax)*scale+dx && out[i*8+1]==ay+(v[1]-ay)*scale+dy);
        CHECK(!memcmp(out+i*8+2,v+2,24));
    }
    /* Repeated native submissions must not leave an unscaled floating copy. */
    for(i=0;i<5;++i) {
        out=make_scaled_ui_vertices(4,0x1c4,mesh[0].bytes+0x28,24,scratch,sizeof(scratch),0,0);
        CHECK((const void*)out==scratch);
        CHECK(out[0]==ax+(600-ax)*scale+dx && out[1]==ay+(400-ay)*scale+dy);
    }
    /* Fingerprints still reject changed geometry; consumed ownership expires
       at the next frame even if the allocation remains identical. */
    ((DWORD*)(mesh[1].bytes+0x28))[23*8]^=1;
    CHECK(make_scaled_ui_vertices(4,0x1c4,mesh[1].bytes+0x28,24,scratch,sizeof(scratch),0,0)==mesh[1].bytes+0x28);
    ++g_ui_present_serial;
    CHECK(make_scaled_ui_vertices(4,0x1c4,mesh[0].bytes+0x28,24,scratch,sizeof(scratch),0,0)==mesh[0].bytes+0x28);
    /* Native countdown drops one triangle at a time, not always 24 vertices. */
    for(i=3;i<=24;i+=3) {
        DWORD j; *(DWORD*)(mesh[0].bytes+0xc)=i;
        owner_cooldown_build_c((void*)123,&known_window,1,2,12,12,mesh[0].bytes,4,5,6);
        for(j=0;j<3;++j) {
            out=make_scaled_ui_vertices(4,0x1c4,mesh[0].bytes+0x28,i,scratch,sizeof(scratch),0,0);
            CHECK((const void*)out==scratch);
            CHECK(out[0]==ax+(600-ax)*scale+dx && out[1]==ay+(400-ay)*scale+dy);
        }
    }
    *(DWORD*)(mesh[0].bytes+0xc)=24;
    /* Unknown window must not borrow a parent's transform. */
    g_owner_bitmap_scope=saved;
    owner_cooldown_build_c((void*)123,&unknown_window,1,2,12,12,mesh[0].bytes,4,5,6);
    CHECK(make_scaled_ui_vertices(4,0x1c4,mesh[0].bytes+0x28,24,scratch,sizeof(scratch),0,0)==mesh[0].bytes+0x28);
    puts("PASS cooldown: concrete hotbar owner overrides buff scope, delayed independent transforms, 24 vertices and attributes, native ABI forwarding, unknown owner exclusion");
 }
int main(void) {
    cooldown_case(125,590,390);
    cooldown_case(150,590,390);
    cooldown_case(200,590,390);
    cooldown_case(200,1700,1000);
    cooldown_case(150,25,25);
}
'''
with tempfile.TemporaryDirectory() as d:
 p=Path(d);(p/'test.c').write_text(prefix+bm.types+bg.stubs+bg.production+prod+tests)
 subprocess.run(['clang','-m32','-std=c11','-O1','-g','-fsanitize=address,undefined',str(p/'test.c'),'-o',str(p/'test')],check=True)
 subprocess.run([str(p/'test')],check=True)
