"""Exercise real per-type panel callbacks and navigation on the render thread."""
from pathlib import Path
import subprocess,tempfile
import test_settings as t
source=Path('prm_uifix.c').read_text()
extra=r'''
#include "ui_window_config.h"
static int s_equal(const char* a,const char* b) { return !strcmp(a,b); }
static void s_append_int(char* out,unsigned int cap,LONG value) {
 if(value<0) {s_append(out,cap,"-");value=-value;}
 s_append_uint(out,cap,(DWORD)value);
}
'''+ '\n'.join(t.extract_function(source,n) for n in ('ui_settings_type_count','ui_settings_type_name','ui_settings_type_value','ui_settings_type_apply'))+r'''
#define UI_SETTINGS_TYPES 1
#define UI_SETTINGS_TYPE_COUNT ui_settings_type_count
#define UI_SETTINGS_TYPE_NAME ui_settings_type_name
#define UI_SETTINGS_TYPE_VALUE ui_settings_type_value
#define UI_SETTINGS_TYPE_APPLY ui_settings_type_apply
'''
tests=t.TESTS.replace('int main(void)','int baseline_main(void)')+r'''
int main(void) {
 reset_core();ready_and_install();
 ui_window_config("UIMinimapZoomWnd",1);ui_window_config("UIShortCutWnd",1);
 open_panel();
 assert(g_ui_settings_target==0);
 ui_settings_change_selected(1);assert(g_ui_settings_target==1);
 assert(g_ui_settings_draft_percent==0);
 g_ui_settings_selected=1;ui_settings_change_selected(-1);
 assert(g_ui_settings_draft_percent==1000);
 g_ui_settings_selected=2;ui_settings_change_selected(1);
 g_ui_settings_selected=3;ui_settings_change_selected(-1);
 ui_settings_queue_draft(0);ui_settings_poll();ui_settings_commit();
 assert(ui_window_percent("UIMinimapZoomWnd",133)==1000);
 assert(ui_window_config("UIMinimapZoomWnd",0)->x==5);
 assert(ui_window_config("UIMinimapZoomWnd",0)->y==-5);
 assert(g_ui_scale_percent==133);
 g_ui_settings_selected=0;ui_settings_change_selected(1);
 assert(g_ui_settings_target==2 && g_ui_settings_draft_x==0);
 g_ui_settings_selected=1;ui_settings_change_selected(1);
 assert(g_ui_settings_draft_percent==100);
 ui_settings_queue_draft(1);ui_settings_poll();ui_settings_commit();
 assert(ui_window_percent("UIShortCutWnd",133)==100);
 assert(ui_window_percent("UIMinimapZoomWnd",133)==1000);
 assert(g_save_calls==4 && window_writes==3*(int)g_ui_window_config_count);
 assert(saved_minimap==1000 && saved_hotbar==100);
 ui_settings_draw_surface(&fake_surface);
 assert(get_dc_calls==1 && release_dc_calls==1);
 assert(first_fill_rect.bottom-first_fill_rect.top==420);
 assert(fill_rect_calls>=2);
 g_ui_settings_selected=0;ui_settings_select_row(-1);assert(g_ui_settings_selected==6);
 ui_settings_select_row(1);assert(g_ui_settings_selected==0);

 /* Applying only crisp must preserve global scale and every per-type pose. */
 for(int target=0;target<ui_settings_type_count();++target) {
  UIWindowConfig before[UI_WINDOW_CONFIG_CAP];
  memcpy(before,g_ui_window_configs,sizeof(before));
  int scale=g_ui_scale_percent,keep=g_ui_keep_on_screen,enabled=g_ui_runtime_enabled;
  g_ui_settings_target=target;ui_settings_load_target();
  g_ui_settings_selected=5;
  for(int toggle=0;toggle<2;++toggle) {
   int crisp=g_ui_sharp_filter;
   ui_settings_change_selected(1);
   ui_settings_queue_draft(0);ui_settings_poll();ui_settings_commit();
   assert(g_ui_sharp_filter!=crisp);
   assert(g_ui_scale_percent==scale && g_ui_keep_on_screen==keep && g_ui_runtime_enabled==enabled);
   assert(!memcmp(before,g_ui_window_configs,sizeof(before)));
  }
 }
 puts("PASS crisp-only panel applies preserve global scale and all per-type scales/positions");
 puts("PASS per-window panel: selector, 1000% minimap/100% hotbar, independent offsets, global unchanged, save-all, row navigation and rendered panel");
}
'''
api=t.API_STUBS.replace('    assert(!strcmp(section,"UI") && !strcmp(path,"fixture.ini"));', r'''    if(!strncmp(section,"Window.",7)) {
        assert(!strcmp(path,"fixture.ini"));++window_writes;
        if(!strcmp(key,"ScalePercent")) {
            if(!strcmp(section,"Window.UIMinimapZoomWnd")) saved_minimap=atoi(value);
            if(!strcmp(section,"Window.UIShortCutWnd")) saved_hotbar=atoi(value);
        }
        return 1;
    }
    assert(!strcmp(section,"UI") && !strcmp(path,"fixture.ini"));''')
harness=t.PREFIX+t.CORE_STUBS+t.CORE+extra+'\n#include "ui_settings.h"\nstatic int window_writes,saved_minimap,saved_hotbar;\n'+api+tests
with tempfile.TemporaryDirectory() as d:
 p=Path(d);(p/'t.c').write_text(harness)
 subprocess.run(['clang','-m32','-std=c11','-O1','-g','-fsanitize=address,undefined','-I',str(t.ROOT),str(p/'t.c'),'-o',str(p/'t')],check=True)
 subprocess.run([str(p/'t')],check=True)
