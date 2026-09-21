"""Per-type preferences, inheritance, persistence reads and bounded keys."""
from pathlib import Path
import subprocess,tempfile
root=Path(__file__).resolve().parent
c=r'''
#include <assert.h>
#include <string.h>
#include <stdio.h>
static int reads;
static int read_ini(const char* section,const char* key,int fallback) {
 ++reads;
 if(!strcmp(section,"Window.UIMinimapZoomWnd") && !strcmp(key,"ScalePercent")) return 300;
 if(!strcmp(section,"Window.UIShortCutWnd") && !strcmp(key,"OffsetX")) return -42;
 return fallback;
}
#define UI_WINDOW_READ read_ini
#include "ui_window_config.h"
int main(void) {
 assert(ui_window_percent("UIMinimapZoomWnd",150)==300);
 assert(ui_window_percent("UIShortCutWnd",150)==150);
 assert(ui_window_config("UIShortCutWnd",0)->x==-42);
 assert(reads==6);
 assert(ui_window_percent("UIMinimapZoomWnd",100)==300 && reads==6);
 assert(ui_window_set("UIShortCutWnd",100,15,-22));
 assert(ui_window_percent("UIShortCutWnd",200)==100);
 assert(ui_window_percent("UIMinimapZoomWnd",200)==300);
 assert(ui_window_set("UIShortCutWnd",0,0,0));
 assert(ui_window_percent("UIShortCutWnd",200)==200);
 assert(ui_window_set("UIShortCutWnd",1000,0,0));
 assert(ui_window_percent("UIShortCutWnd",200)==1000);
 assert(!ui_window_set("UIShortCutWnd",1001,0,0));
 assert(!ui_window_set("UIShortCutWnd",99,0,0));
 assert(ui_window_set("UIShortCutWnd",250,999999,-999999));
 assert(ui_window_config("UIShortCutWnd",0)->x==8192);
 assert(ui_window_config("UIShortCutWnd",0)->y==-8192);
 char name[80];memset(name,'x',79);name[79]=0;
 assert(!ui_window_config(name,1));
 while(g_ui_window_config_count<UI_WINDOW_CONFIG_CAP) {
  sprintf(name,"Window%u",g_ui_window_config_count);
  assert(ui_window_config(name,1));
 }
 assert(!ui_window_config("Overflow",1));
 assert(ui_window_percent("UIMinimapZoomWnd",100)==300);
 puts("PASS per-type preferences: minimap 300%, hotbar 100%, global inheritance, cached INI reads, offsets and capacity");
}
'''
with tempfile.TemporaryDirectory() as d:
 p=Path(d);(p/'test.c').write_text(c)
 subprocess.run(['clang','-std=c11','-fsanitize=address,undefined','-I',str(root),str(p/'test.c'),'-o',str(p/'test')],check=True)
 subprocess.run([str(p/'test')],check=True)
