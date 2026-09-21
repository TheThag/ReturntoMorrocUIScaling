"""Independent window transforms, offsets and input round trips."""
from pathlib import Path
import tempfile,subprocess
import test_background as bg
import test_bitmap as bm
extra=bm.struct_type('OwnerInputRegion')+'\n'+ '\n'.join(bm.function(n) for n in ('owner_input_region_bounds','owner_input_map_region'))
tests=bg.tests.replace('int main(void)','int baseline_main(void)')+r'''
int main(void) {
    DWORD n,i; NativeWindow* windows[2]={&known_window,&second_window};
    const char* names[2]={"UIMinimapZoomWnd","UIShortCutWnd"};
    float expected[2]={10,1},last_x[2],last_y[2];
    reset_all();g_ui_scale_percent=150;g_ui_keep_on_screen=0;g_ui_screen_w=3440;g_ui_screen_h=1440;
    CHECK(ui_window_set(names[0],1000,-40,25));CHECK(ui_window_set(names[1],100,70,-30));
    for(i=0;i<2;++i) {
        native_window_set(windows[i],200+i*400,200,128,100);
        strcpy(owner_state_for((DWORD)(ULONG_PTR)windows[i],1)->class_name,names[i]);
    }
    for(n=0;n<20;++n) for(i=0;i<2;++i) {
        OwnerInputRegion r={0};POINT p;UIRectF b;Quad q,out;
        OwnerWindowState* st=owner_state_for((DWORD)(ULONG_PTR)windows[i],0);
        CHECK(owner_bitmap_prepare(st->object_ptr,200+i*400,200,128,100));
        CHECK(g_owner_bitmap_scope.fit_scale==expected[i]);
        r.ax=st->ax;r.ay=st->ay;r.fit_scale=st->fit_scale;
        r.offset_x=st->offset_x;r.offset_y=st->offset_y;
        r.rect=(UIRectF){200+i*400,200,328+i*400,300};
        owner_input_region_bounds(&r,&b);
        if(!n) {last_x[i]=b.l;last_y[i]=b.t;}
        CHECK(b.l==last_x[i] && b.t==last_y[i]);
        CHECK(b.r-b.l==128*expected[i] && b.b-b.t==100*expected[i]);
        p.x=(LONG)(b.l+60*expected[i]);p.y=(LONG)(b.t+40*expected[i]);
        CHECK(owner_input_map_region(&p,&r));
        CHECK(p.x==260+(LONG)i*400 && p.y==240);
        memset(&q,0,sizeof(q));
        for(DWORD j=0;j<4;++j) {q.f[j][0]=r.rect.l+(j&1)*128;q.f[j][1]=r.rect.t+(j>>1)*100;q.f[j][3]=1;}
        owner_bitmap_note_vertices(&q,4,&g_owner_bitmap_scope);
        CHECK(scaled(&q,&out)==&out);CHECK(out.f[0][0]==b.l && out.f[0][1]==b.t);
    }
    /* Moving an otherwise immovable widget changes its visual and hit origin once. */
    CHECK(ui_window_set(names[0],1000,-10,45));
    CHECK(owner_bitmap_prepare((DWORD)(ULONG_PTR)&known_window,200,200,128,100));
    CHECK(g_owner_bitmap_scope.ax+(200-g_owner_bitmap_scope.ax)*10+g_owner_bitmap_scope.offset_x==last_x[0]+30);
    CHECK(g_owner_bitmap_scope.ay+(200-g_owner_bitmap_scope.ay)*10+g_owner_bitmap_scope.offset_y==last_y[0]+20);
    puts("PASS independent rendered windows: minimap 1000%, hotbar 100%, repeated-position stability, user movement and matching inverse input");
}
'''
with tempfile.TemporaryDirectory() as d:
 p=Path(d);(p/'t.c').write_text(bg.prefix+bm.types+bg.stubs+bg.production+extra+tests)
 subprocess.run(['clang','-m32','-std=c11','-O1','-g','-fsanitize=address,undefined',str(p/'t.c'),'-o',str(p/'t')],check=True)
 subprocess.run([str(p/'t')],check=True)
