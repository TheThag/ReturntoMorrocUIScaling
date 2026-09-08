#!/usr/bin/env python3
"""Exercise the render-thread in-game settings overlay and mailbox contract."""

import os
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parent


def extract_function(source, name):
    marker = "static "
    start = source.find(marker)
    while start >= 0:
        line_end = source.find("\n", start)
        line = source[start:line_end if line_end >= 0 else len(source)]
        if f" {name}(" in line:
            opening = source.find("{", start, line_end if line_end >= 0 else len(source))
            if opening < 0:
                raise ValueError(f"missing body for {name}")
            depth = 0
            i = opening
            in_string = None
            in_comment = None
            while i < len(source):
                if in_comment == "block":
                    if source[i:i + 2] == "*/":
                        in_comment = None
                        i += 2
                        continue
                    i += 1
                    continue
                if in_comment == "line":
                    if source[i] == "\n":
                        in_comment = None
                    i += 1
                    continue
                if in_string:
                    if source[i] == "\\":
                        i += 2
                        continue
                    if source[i] == in_string:
                        in_string = None
                    i += 1
                    continue
                if source[i:i + 2] == "/*":
                    in_comment = "block"
                    i += 2
                    continue
                if source[i:i + 2] == "//":
                    in_comment = "line"
                    i += 2
                    continue
                if source[i] in "\"'":
                    in_string = source[i]
                elif source[i] == "{":
                    depth += 1
                elif source[i] == "}":
                    depth -= 1
                    if depth == 0:
                        return source[start:i + 1]
                i += 1
        start = source.find(marker, start + len(marker))
    raise ValueError(f"missing function {name}")


SOURCE = (ROOT / "prm_uifix.c").read_text()
CORE = "\n\n".join(extract_function(SOURCE, name) for name in (
    "ui_settings_apply", "ui_settings_commit"))

PREFIX = r'''
#include <assert.h>
#include <stdint.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef uint8_t BYTE;
typedef uint16_t WORD;
typedef uint32_t UINT;
typedef int32_t LONG;
typedef uint32_t DWORD;
typedef uintptr_t ULONG_PTR;
typedef uintptr_t SIZE_T;
typedef void *HANDLE;
typedef void *HMODULE;
typedef void *HINSTANCE;
typedef void *LPVOID;
typedef const char *LPCSTR;
typedef char *LPSTR;
typedef const void *LPCVOID;
typedef void *HWND;
typedef int BOOL;
typedef LONG HRESULT;
typedef struct { LONG x,y; } POINT;
typedef struct { LONG left,top,right,bottom; } RECT;
#define WINAPI __attribute__((stdcall))
#define PRM_MAIN_HWND_RVA 0x00D0AABCUL
#define PRM_UI_CAPTURE_RVA 0x00AB786CUL
#define FAKE_EXE_SIZE (PRM_MAIN_HWND_RVA+4UL)

static HMODULE g_exe;
static DWORD g_exe_size;
static char g_ini_path[520] = "fixture.ini";
static HWND g_input_hwnd;
static int g_ui_scale_percent=133;
static int g_ui_enabled=1;
static int g_ui_runtime_enabled=1;
static int g_ui_sharp_filter=0;
static int g_ui_keep_on_screen=1;
static int g_ui_screen_w=1920;
static int g_ui_screen_h=1080;
static DWORD g_fake_capture;
static int g_log_count;
static char g_last_log[320];
static int g_save_calls;
static int g_save_fail_at;
static char g_save_keys[4][32];
static char g_save_values[4][32];
static BYTE g_fake_exe[FAKE_EXE_SIZE];
static void *g_surface_vtable[27];
static void *g_fake_surface_address;

static LONG WINAPI fake_set_window_long(HWND,int,LONG);
typedef LONG (WINAPI *TEST_WNDPROC)(HWND,DWORD,ULONG_PTR,LONG);
static LONG WINAPI fake_call_window_proc(TEST_WNDPROC,HWND,DWORD,ULONG_PTR,LONG);
static BOOL WINAPI fake_write_profile(const char*,const char*,const char*,const char*);
static int WINAPI fake_save_dc(void*);
static BOOL WINAPI fake_restore_dc(void*,int);
static void* WINAPI fake_create_brush(DWORD);
static int WINAPI fake_fill_rect(void*,const RECT*,void*);
static BOOL WINAPI fake_delete_object(void*);
static void* WINAPI fake_select_object(void*,void*);
static int WINAPI fake_set_bk_mode(void*,int);
static DWORD WINAPI fake_set_text_color(void*,DWORD);
static BOOL WINAPI fake_text_out(void*,int,int,const char*,int);
static int WINAPI fake_draw_text(void*,const char*,int,RECT*,UINT);
static void* WINAPI fake_create_font(int,int,int,int,int,DWORD,DWORD,DWORD,DWORD,DWORD,DWORD,DWORD,DWORD,const char*);

static int range_in(const void *p, size_t bytes, const void *base, size_t size) {
    uintptr_t q=(uintptr_t)p,b=(uintptr_t)base;
    return p && q>=b && bytes<=size && q-b<=size-bytes;
}
static int mem_readable(const void *p,DWORD bytes) {
    if (range_in(p,bytes,g_fake_exe,sizeof(g_fake_exe))) return 1;
    if (range_in(p,bytes,g_surface_vtable,27*sizeof(void*))) return 1;
    if (p==g_fake_surface_address && bytes<=sizeof(void*)) return 1;
    return 0;
}
static HMODULE find_loaded_module(const char *name) {
    (void)name; return (HMODULE)(ULONG_PTR)0x12340000UL;
}
static void *resolve_export(HMODULE module,const char *name) {
    (void)module;
    if (!strcmp(name,"SetWindowLongA")) return (void*)fake_set_window_long;
    if (!strcmp(name,"CallWindowProcA")) return (void*)fake_call_window_proc;
    if (!strcmp(name,"SaveDC")) return (void*)fake_save_dc;
    if (!strcmp(name,"RestoreDC")) return (void*)fake_restore_dc;
    if (!strcmp(name,"CreateSolidBrush")) return (void*)fake_create_brush;
    if (!strcmp(name,"FillRect")) return (void*)fake_fill_rect;
    if (!strcmp(name,"DeleteObject")) return (void*)fake_delete_object;
    if (!strcmp(name,"SelectObject")) return (void*)fake_select_object;
    if (!strcmp(name,"SetBkMode")) return (void*)fake_set_bk_mode;
    if (!strcmp(name,"SetTextColor")) return (void*)fake_set_text_color;
    if (!strcmp(name,"TextOutA")) return (void*)fake_text_out;
    if (!strcmp(name,"DrawTextA")) return (void*)fake_draw_text;
    if (!strcmp(name,"CreateFontA")) return (void*)fake_create_font;
    if (!strcmp(name,"WritePrivateProfileStringA")) return (void*)fake_write_profile;
    return 0;
}
static void s_append(char *dst,unsigned int cap,const char *src) {
    unsigned int i=0,j=0;
    if (!dst || !cap || !src) return;
    while (i+1<cap && dst[i]) ++i;
    while (i+1<cap && src[j]) dst[i++]=src[j++];
    if (i<cap) dst[i]=0;
}
static void s_append_uint(char *dst,unsigned int cap,DWORD value) {
    char temp[16]; unsigned int n=0;
    if (!value) { s_append(dst,cap,"0"); return; }
    while (value && n<sizeof(temp)) { temp[n++]=(char)('0'+value%10); value/=10; }
    while (n) { char one[2]={temp[--n],0}; s_append(dst,cap,one); }
}
static void log_line(const char *line) {
    ++g_log_count; s_append(g_last_log,sizeof(g_last_log),line);
}
static DWORD owner_native_capture(void) { return g_fake_capture; }
'''

CORE_STUBS = r'''
#define UIHK_OVERLAY      0
#define UIHK_FILTER       1
#define UIHK_SCALE        2
#define UIHK_INPUT        3
#define UIHK_GROUPS       4
#define UIHK_DIAGNOSTICS  5
#define UIHK_WORLD        6
#define UIHK_TRACE        7
#define UIHK_VIRTUAL_TRACE 8
#define UIHK_COUNT        9
#define UIHK_SHIFT        1UL
#define UIHK_CTRL         2UL
#define UIHK_ALT          4UL
#define UIHK_WIN          8UL

static DWORD g_hotkey_vk[UIHK_COUNT];
static DWORD g_hotkey_mods[UIHK_COUNT];
static DWORD g_hotkey_bound[UIHK_COUNT];
static DWORD g_hotkey_current_mods;
static DWORD g_hotkey_queue;
static DWORD g_hotkey_queue_calls;

static void hotkeys_reset(void) {
    unsigned int i;
    for (i=0; i<UIHK_COUNT; ++i) {
        g_hotkey_vk[i]=0; g_hotkey_mods[i]=0; g_hotkey_bound[i]=0;
    }
    /* The shipped default is deliberately distinct from the old F2/F3/F5
       polling shortcuts: Shift+P opens the overlay. */
    g_hotkey_vk[UIHK_OVERLAY]=(DWORD)'P';
    g_hotkey_mods[UIHK_OVERLAY]=1;
    g_hotkey_bound[UIHK_OVERLAY]=1;
    g_hotkey_current_mods=0; g_hotkey_queue=0; g_hotkey_queue_calls=0;
}
static void hotkeys_bind(unsigned int action, DWORD vk, DWORD mods) {
    assert(action<UIHK_COUNT);
    g_hotkey_vk[action]=vk; g_hotkey_mods[action]=mods;
    g_hotkey_bound[action]=(vk!=0);
}
static void hotkeys_clear(unsigned int action) {
    assert(action<UIHK_COUNT);
    g_hotkey_vk[action]=0; g_hotkey_mods[action]=0; g_hotkey_bound[action]=0;
}
static DWORD ui_hotkeys_modifiers(void) { return g_hotkey_current_mods; }
static DWORD ui_hotkeys_match(DWORD vk, DWORD mods) {
    unsigned int i; DWORD mask=0;
    for (i=0; i<UIHK_COUNT; ++i)
        if (g_hotkey_bound[i] && g_hotkey_vk[i]==vk && g_hotkey_mods[i]==mods)
            mask |= 1UL<<i;
    return mask;
}
static void ui_hotkeys_queue(DWORD mask) {
    g_hotkey_queue |= mask; ++g_hotkey_queue_calls;
}
static int ui_hotkey_take(unsigned int action) {
    DWORD bit = action<32U ? (1UL<<action) : 0;
    int result=(g_hotkey_queue & bit)!=0;
    g_hotkey_queue &= ~bit;
    return result;
}

static int g_settings_request_valid,g_settings_request_scale,g_settings_request_enabled;
static int g_settings_request_crisp,g_settings_request_keep,g_settings_request_save;
'''

API_STUBS = r'''
static HWND game_window=(HWND)(ULONG_PTR)0x1010;
static struct { void **vt; } fake_surface;
static void *fake_dc=(void*)(ULONG_PTR)0x6060UL;
static int set_window_long_calls;
static int set_window_long_fails;
static HWND last_subclass_hwnd;
static LONG last_subclass_proc;
static int call_window_proc_calls;
static int old_proc_result=0x42;
static int get_dc_calls,release_dc_calls;
static int get_dc_fails,release_dc_fails;
static int save_dc_calls,restore_dc_calls,save_dc_fails,restore_dc_fails;
static int fill_rect_calls,fill_rect_fail_at;
static RECT first_fill_rect;
static int brush_calls,delete_object_calls,delete_object_fails;
static int select_calls;
static int bk_mode_calls,text_color_calls,text_out_calls,draw_text_calls;
static int text_out_fail,draw_text_fail_at;
static int create_font_calls,create_font_fails,created_font_height;
static int fail_gdi_api;
static int surface_ready;

static HRESULT WINAPI fake_surface_get_dc(void *self,void **out) {
    assert(self==(void*)&fake_surface); ++get_dc_calls;
    if (out) *out=fake_dc;
    if (get_dc_fails) return (HRESULT)-1;
    return 0;
}
static HRESULT WINAPI fake_surface_release_dc(void *self,void *dc) {
    assert(self==(void*)&fake_surface); assert(dc==fake_dc || dc==0);
    ++release_dc_calls; return release_dc_fails?(HRESULT)-1:0;
}
static LONG WINAPI fake_set_window_long(HWND hwnd,int index,LONG proc) {
    assert(index==UISET_GWL_WNDPROC); ++set_window_long_calls;
    last_subclass_hwnd=hwnd; last_subclass_proc=proc;
    return set_window_long_fails?0:(LONG)0x41414141UL;
}
static LONG WINAPI fake_call_window_proc(TEST_WNDPROC proc,HWND hwnd,DWORD message,ULONG_PTR wp,LONG lp) {
    (void)proc; (void)hwnd; (void)message; (void)wp; (void)lp;
    ++call_window_proc_calls; return old_proc_result;
}
static int WINAPI fake_save_dc(void *dc) { assert(dc==fake_dc); ++save_dc_calls; return save_dc_fails?0:17; }
static BOOL WINAPI fake_restore_dc(void *dc,int saved) { assert(dc==fake_dc); assert(saved==17); ++restore_dc_calls; return restore_dc_fails?0:1; }
static void *WINAPI fake_create_brush(DWORD color) { (void)color; ++brush_calls; return (void*)(ULONG_PTR)(0x7000UL+(DWORD)brush_calls); }
static int WINAPI fake_fill_rect(void *dc,const RECT *rect,void *brush) {
    assert(dc==fake_dc && brush); if (!fill_rect_calls) first_fill_rect=*rect;
    ++fill_rect_calls; return fill_rect_fail_at && fill_rect_calls==fill_rect_fail_at?0:1;
}
static BOOL WINAPI fake_delete_object(void *object) { assert(object); ++delete_object_calls; return delete_object_fails?0:1; }
static void *WINAPI fake_select_object(void *dc,void *object) {
    assert(dc==fake_dc && object); ++select_calls;
    return (select_calls==1)?(void*)(ULONG_PTR)0x8888UL:(void*)(ULONG_PTR)0x9999UL;
}
static int WINAPI fake_set_bk_mode(void *dc,int mode) { assert(dc==fake_dc && mode==UISET_TRANSPARENT); ++bk_mode_calls; return 1; }
static DWORD WINAPI fake_set_text_color(void *dc,DWORD color) { assert(dc==fake_dc && color==0x00ffffffUL); ++text_color_calls; return 0; }
static BOOL WINAPI fake_text_out(void *dc,int x,int y,const char *text,int length) {
    (void)x; (void)y; (void)text; (void)length; assert(dc==fake_dc); ++text_out_calls; return !text_out_fail;
}
static int WINAPI fake_draw_text(void *dc,const char *text,int length,RECT *rect,UINT flags) {
    (void)text; (void)length; (void)rect; (void)flags; assert(dc==fake_dc); ++draw_text_calls;
    return draw_text_fail_at && draw_text_calls==draw_text_fail_at?0:1;
}
static void *WINAPI fake_create_font(int height,int width,int escapement,int orientation,int weight,
                                     DWORD italic,DWORD underline,DWORD strike,DWORD charset,
                                     DWORD out_precision,DWORD clip_precision,DWORD quality,
                                     DWORD pitch,const char *face) {
    (void)width; (void)escapement; (void)orientation; (void)weight; (void)italic;
    (void)underline; (void)strike; (void)charset; (void)out_precision;
    (void)clip_precision; (void)quality; (void)pitch; (void)face;
    ++create_font_calls; created_font_height=height;
    return create_font_fails?0:(void*)(ULONG_PTR)0x7777UL;
}
static BOOL WINAPI fake_write_profile(const char *section,const char *key,const char *value,const char *path) {
    assert(!strcmp(section,"UI") && !strcmp(path,"fixture.ini"));
    assert(g_save_calls<4);
    strncpy(g_save_keys[g_save_calls],key,sizeof(g_save_keys[0])-1);
    strncpy(g_save_values[g_save_calls],value,sizeof(g_save_values[0])-1);
    if (g_save_fail_at==g_save_calls) { ++g_save_calls; return 0; }
    ++g_save_calls; return 1;
}
static void reset_fake(void) {
    unsigned int i;
    memset(g_fake_exe,0,sizeof(g_fake_exe));
    memset(g_surface_vtable,0,sizeof(g_surface_vtable));
    fake_surface.vt=g_surface_vtable;
    g_fake_surface_address=&fake_surface;
    g_surface_vtable[17]=(void*)fake_surface_get_dc;
    g_surface_vtable[26]=(void*)fake_surface_release_dc;
    *(DWORD*)(g_fake_exe+PRM_MAIN_HWND_RVA)=(DWORD)(ULONG_PTR)game_window;
    g_exe=g_fake_exe; g_exe_size=sizeof(g_fake_exe); g_input_hwnd=game_window;
    g_ui_screen_w=1920; g_ui_screen_h=1080;
    g_ui_scale_percent=133; g_ui_runtime_enabled=1; g_ui_sharp_filter=0; g_ui_keep_on_screen=1;
    g_fake_capture=0; g_log_count=0; g_last_log[0]=0;
    g_save_calls=0; g_save_fail_at=-1; memset(g_save_keys,0,sizeof(g_save_keys)); memset(g_save_values,0,sizeof(g_save_values));
    set_window_long_calls=set_window_long_fails=0; last_subclass_hwnd=0; last_subclass_proc=0;
    call_window_proc_calls=0; get_dc_calls=release_dc_calls=0; get_dc_fails=release_dc_fails=0;
    save_dc_calls=restore_dc_calls=save_dc_fails=restore_dc_fails=0; fill_rect_calls=fill_rect_fail_at=0;
    memset(&first_fill_rect,0,sizeof(first_fill_rect)); brush_calls=delete_object_calls=delete_object_fails=0;
    select_calls=bk_mode_calls=text_color_calls=text_out_calls=draw_text_calls=0;
    text_out_fail=draw_text_fail_at=0; create_font_calls=create_font_fails=created_font_height=0; fail_gdi_api=0; surface_ready=1;
    g_settings_request_valid=0; g_settings_request_scale=0; g_settings_request_enabled=0;
    g_settings_request_crisp=0; g_settings_request_keep=0; g_settings_request_save=0;
    hotkeys_reset();
    g_ui_settings_api_state=0; g_ui_settings_subclass_state=0; g_ui_settings_panel_open=0;
    g_ui_settings_deferred_open=0; g_ui_settings_events=0; g_ui_settings_mailbox=0;
    g_ui_settings_snapshot=0; g_ui_settings_game_hwnd_snapshot=0; g_ui_settings_original_wndproc=0;
    g_ui_settings_bound_hwnd=0; g_ui_settings_selected=0; g_ui_settings_draft_percent=0;
    g_ui_settings_draft_enabled=0; g_ui_settings_draft_crisp=0; g_ui_settings_draft_keep=0;
    g_ui_settings_status=0; g_ui_settings_failure_logged=0;
    g_ui_settings_set_window_long=0; g_ui_settings_call_window_proc=0;
    g_ui_settings_get_dc=0; g_ui_settings_release_dc=0; g_ui_settings_save_dc=0; g_ui_settings_restore_dc=0;
    g_ui_settings_create_brush=0; g_ui_settings_fill_rect=0; g_ui_settings_delete_object=0;
    g_ui_settings_select_object=0; g_ui_settings_set_bk_mode=0; g_ui_settings_set_text_color=0;
    g_ui_settings_text_out=0; g_ui_settings_draw_text=0; g_ui_settings_create_font=0;
    ui_settings_key_state_clear();
    for(i=0;i<4;++i) { g_save_keys[i][0]=0; g_save_values[i][0]=0; }
}
static void reset_core(void) { reset_fake(); }
static void ready_and_install(void) { ui_settings_poll(); assert(g_ui_settings_subclass_state==2); }
static UISettingsLResult send_key(DWORD message, DWORD key, DWORD mods, DWORD flags) {
    g_hotkey_current_mods=mods;
    return ui_settings_wndproc(game_window,message,key,flags);
}
static void press(DWORD key) {
    assert(send_key(UISET_WM_KEYDOWN,key,0,0)==0);
    ui_settings_poll();
}
static void press_overlay(void) {
    assert(send_key(UISET_WM_KEYDOWN,(DWORD)'P',1,0)==0);
    ui_settings_poll();
    assert(send_key(UISET_WM_KEYUP,(DWORD)'P',0,0)==0);
    assert(send_key(UISET_WM_CHAR,(DWORD)'P',0,0)==0);
}
static void open_panel(void) { press_overlay(); assert(ui_settings_is_open()); }
'''

TESTS = r'''
static void test_parser_and_packet(void) {
    int value=0;
    assert(ui_settings_parse_percent("100",&value) && value==100);
    assert(ui_settings_parse_percent(" 200 ",&value) && value==200);
    assert(!ui_settings_parse_percent("99",&value));
    assert(!ui_settings_parse_percent("201",&value));
    assert(!ui_settings_parse_percent("133x",&value));
    assert((ui_settings_pack(50,1,0,1,1)&UISET_PACKET_PERCENT)==100);
    assert((ui_settings_pack(250,0,1,0,0)&UISET_PACKET_PERCENT)==200);
    puts("PASS: settings percent validation, clamp, and packed fields");
}

static void test_game_hwnd_subclass_and_retry(void) {
    reset_core();
    assert(ui_settings_game_hwnd()==game_window);
    ready_and_install();
    assert(set_window_long_calls==1 && last_subclass_hwnd==game_window);
    assert(last_subclass_proc==(LONG)(ULONG_PTR)ui_settings_wndproc);

    reset_core();
    *(DWORD*)(g_fake_exe+PRM_MAIN_HWND_RVA)=0; g_input_hwnd=0;
    ui_settings_poll();
    assert(g_ui_settings_subclass_state==0 && set_window_long_calls==0);
    *(DWORD*)(g_fake_exe+PRM_MAIN_HWND_RVA)=(DWORD)(ULONG_PTR)game_window;
    ui_settings_poll();
    assert(g_ui_settings_subclass_state==2 && set_window_long_calls==1);

    reset_core(); set_window_long_fails=1; ui_settings_poll();
    assert(g_ui_settings_subclass_state==3 && !ui_settings_is_open());
    puts("PASS: render thread resolves the native main HWND, subclasses once, and retries a late HWND");
}

static void test_deferred_open_and_key_routing(void) {
    reset_core(); ready_and_install();
    g_fake_capture=1;
    press_overlay();
    assert(!ui_settings_is_open() && g_ui_settings_deferred_open);
    /* A second overlay binding while capture is active cancels the pending open. */
    press_overlay();
    assert(!ui_settings_is_open() && !g_ui_settings_deferred_open);
    g_fake_capture=0; ui_settings_poll();
    assert(!ui_settings_is_open());
    press_overlay();
    assert(ui_settings_is_open() && !g_ui_settings_deferred_open);

    assert(ui_settings_wndproc(game_window,UISET_WM_KEYDOWN,0x41,0)==0);
    assert(ui_settings_wndproc(game_window,UISET_WM_CHAR,0x61,0)==0);
    assert(ui_settings_wndproc(game_window,UISET_WM_LBUTTONDOWN,0,0)==0);
    assert(ui_settings_wndproc(game_window,UISET_WM_MOUSEWHEEL,0,0)==0);
    assert(ui_settings_wndproc(game_window,UISET_WM_LBUTTONDBLCLK,0,0)==0);
    assert(ui_settings_wndproc(game_window,UISET_WM_RBUTTONDBLCLK,0,0)==0);
    assert(ui_settings_wndproc(game_window,UISET_WM_MBUTTONDBLCLK,0,0)==0);
    assert(ui_settings_wndproc(game_window,UISET_WM_XBUTTONDBLCLK,0,0)==0);
    assert(ui_settings_wndproc(game_window,UISET_WM_MOUSEHWHEEL,0,0)==0);
    assert(ui_settings_wndproc(game_window,UISET_WM_KEYUP,0x41,0)==old_proc_result);
    assert(ui_settings_wndproc(game_window,UISET_WM_LBUTTONUP,0,0)==old_proc_result);
    assert(ui_settings_wndproc(game_window,UISET_WM_SYSKEYDOWN,UISET_VK_F4,UISET_ALT_CONTEXT)==old_proc_result);
    assert(call_window_proc_calls==3);
    assert(ui_settings_wndproc(game_window,0x0010,0,0)==old_proc_result);

    assert(send_key(UISET_WM_KEYDOWN,(DWORD)'P',1,UISET_KEY_REPEAT)==0);
    ui_settings_poll(); assert(ui_settings_is_open());
    assert(ui_settings_wndproc(game_window,UISET_WM_NCDESTROY,0,0)==old_proc_result);
    assert(call_window_proc_calls==5);
    assert(!ui_settings_is_open() && !g_ui_settings_original_wndproc && !g_ui_settings_bound_hwnd);
    puts("PASS: capture defers overlay open; open panel blocks key/mouse-down input while key-up, lifecycle, and Alt+F4 pass through");
}

static void test_configurable_hotkey_dispatch(void) {
    int before_calls;

    /* The default Shift+P binding is exact: plain P, F2, F3, and a different
       modifier chord remain ordinary game input while the panel is closed. */
    reset_core(); ready_and_install();
    before_calls=call_window_proc_calls;
    assert(send_key(UISET_WM_KEYDOWN,(DWORD)'P',0,0)==old_proc_result);
    assert(send_key(UISET_WM_CHAR,(DWORD)'p',0,0)==old_proc_result);
    assert(send_key(UISET_WM_KEYUP,(DWORD)'P',0,0)==old_proc_result);
    assert(send_key(UISET_WM_KEYDOWN,0x71UL,0,0)==old_proc_result); /* F2 */
    assert(send_key(UISET_WM_KEYDOWN,0x72UL,0,0)==old_proc_result); /* F3 */
    assert(send_key(UISET_WM_KEYDOWN,(DWORD)'P',3,0)==old_proc_result); /* Ctrl+Shift+P */
    assert(call_window_proc_calls==before_calls+6 && !g_hotkey_queue_calls);
    assert(send_key(UISET_WM_KEYDOWN,(DWORD)'P',1,0)==0);
    assert(send_key(UISET_WM_KEYUP,(DWORD)'P',0,0)==0);
    assert(send_key(UISET_WM_CHAR,(DWORD)'P',0,0)==0);
    ui_settings_poll(); assert(ui_settings_is_open());
    ui_settings_close_panel();

    /* Rebinding is action-index based and queues only while the panel is
       closed.  Autorepeat is consumed without a second queue operation. */
    reset_core(); ready_and_install();
    hotkeys_clear(UIHK_OVERLAY);
    hotkeys_bind(UIHK_OVERLAY,0x72UL,0); /* alternate overlay: F3 */
    hotkeys_bind(UIHK_FILTER,(DWORD)'Q',UIHK_CTRL);
    before_calls=call_window_proc_calls;
    assert(send_key(UISET_WM_KEYDOWN,0x71UL,0,0)==old_proc_result); /* old F2 */
    assert(send_key(UISET_WM_KEYDOWN,0x72UL,0,0)==0);
    assert(send_key(UISET_WM_KEYDOWN,0x72UL,0,UISET_KEY_REPEAT)==0);
    assert(g_hotkey_queue_calls==0);
    assert(send_key(UISET_WM_KEYUP,0x72UL,0,0)==0);
    ui_settings_poll(); assert(ui_settings_is_open());
    ui_settings_close_panel();
    assert(send_key(UISET_WM_KEYDOWN,(DWORD)'Q',UIHK_CTRL,0)==0);
    assert(g_hotkey_queue_calls==1 &&
           (g_hotkey_queue & (1UL<<UIHK_FILTER))!=0);
    assert(send_key(UISET_WM_KEYDOWN,(DWORD)'Q',UIHK_CTRL,UISET_KEY_REPEAT)==0);
    assert(g_hotkey_queue_calls==1);
    assert(send_key(UISET_WM_KEYUP,(DWORD)'Q',0,0)==0);
    assert(ui_hotkey_take(UIHK_FILTER));
    assert(call_window_proc_calls==before_calls+1);

    /* A blank binding leaves both key and character messages untouched. */
    reset_core(); ready_and_install();
    hotkeys_clear(UIHK_OVERLAY); hotkeys_clear(UIHK_FILTER);
    before_calls=call_window_proc_calls;
    assert(send_key(UISET_WM_KEYDOWN,(DWORD)'Q',0,0)==old_proc_result);
    assert(send_key(UISET_WM_CHAR,(DWORD)'q',0,0)==old_proc_result);
    assert(send_key(UISET_WM_KEYUP,(DWORD)'Q',0,0)==old_proc_result);
    assert(call_window_proc_calls==before_calls+3 && !g_hotkey_queue_calls);
    puts("PASS: exact default/alternate/blank bindings dispatch through the configurable hotkey contract with repeat suppression");
}

static void test_hotkey_provenance_and_lifecycle(void) {
    int before_calls;
    DWORD scan_p=0x19UL<<16, scan_digit=0x02UL<<16;

    /* The activation character can arrive after the key-up and after a
       capture-deferred open.  Its scan-tagged pending record keeps it out of
       chat without globally blocking ordinary WM_CHAR messages. */
    reset_core(); ready_and_install(); g_fake_capture=1;
    before_calls=call_window_proc_calls;
    assert(send_key(UISET_WM_KEYDOWN,(DWORD)'P',1,0)==0);
    ui_settings_poll(); assert(g_ui_settings_deferred_open && !ui_settings_is_open());
    assert(send_key(UISET_WM_KEYUP,(DWORD)'P',0,0)==0);
    assert(send_key(UISET_WM_CHAR,(DWORD)'P',0,0)==0);
    assert(call_window_proc_calls==before_calls);
    g_fake_capture=0; ui_settings_poll(); assert(ui_settings_is_open());

    /* Closing has the same delayed-character requirement. */
    before_calls=call_window_proc_calls;
    assert(send_key(UISET_WM_KEYDOWN,(DWORD)'P',1,0)==0);
    ui_settings_poll(); assert(!ui_settings_is_open());
    assert(send_key(UISET_WM_KEYUP,(DWORD)'P',0,0)==0);
    assert(send_key(UISET_WM_CHAR,(DWORD)'P',0,0)==0);
    assert(call_window_proc_calls==before_calls);

    /* Releasing the modifier first must not make the bound key-up leak. */
    reset_core(); ready_and_install();
    assert(send_key(UISET_WM_KEYDOWN,(DWORD)'P',1,0)==0);
    assert(send_key(UISET_WM_KEYUP,(DWORD)'P',0,0)==0);
    assert(send_key(UISET_WM_CHAR,(DWORD)'p',0,0)==0);
    ui_settings_poll(); assert(ui_settings_is_open());
    ui_settings_close_panel();

    /* A scan code is authoritative when translated text changes with the
       modifier state (Shift+1 produces '!'); repeated printable key-downs
       get one suppression record each. */
    reset_core(); ready_and_install();
    hotkeys_clear(UIHK_OVERLAY);
    hotkeys_bind(UIHK_OVERLAY,(DWORD)'1',UIHK_SHIFT);
    assert(send_key(UISET_WM_KEYDOWN,(DWORD)'1',UIHK_SHIFT,scan_digit)==0);
    assert(send_key(UISET_WM_KEYDOWN,(DWORD)'1',UIHK_SHIFT,
                    scan_digit|UISET_KEY_REPEAT)==0);
    assert(send_key(UISET_WM_KEYUP,(DWORD)'1',0,scan_digit)==0);
    assert(send_key(UISET_WM_CHAR,(DWORD)'!',0,scan_digit)==0);
    assert(send_key(UISET_WM_CHAR,(DWORD)'!',0,scan_digit)==0);
    ui_settings_poll(); assert(ui_settings_is_open());
    ui_settings_close_panel();

    /* Alt chords use the SYSCHAR stream but retain the same scan provenance. */
    reset_core(); ready_and_install();
    hotkeys_clear(UIHK_OVERLAY);
    hotkeys_bind(UIHK_OVERLAY,(DWORD)'Q',UIHK_ALT);
    assert(send_key(UISET_WM_SYSKEYDOWN,(DWORD)'Q',UIHK_ALT,scan_p)==0);
    assert(send_key(UISET_WM_SYSKEYUP,(DWORD)'Q',0,scan_p)==0);
    assert(send_key(UISET_WM_SYSCHAR,(DWORD)'q',0,scan_p)==0);
    ui_settings_poll(); assert(ui_settings_is_open());
    ui_settings_close_panel();

    /* If a matched key never produces a character, a fresh ordinary keydown
       for that VK retires its bounded record before forwarding text. */
    reset_core(); ready_and_install();
    assert(send_key(UISET_WM_KEYDOWN,(DWORD)'P',UIHK_SHIFT,scan_p)==0);
    assert(send_key(UISET_WM_KEYUP,(DWORD)'P',0,scan_p)==0);
    assert(send_key(UISET_WM_KEYDOWN,(DWORD)'P',0,scan_p)==old_proc_result);
    assert(send_key(UISET_WM_CHAR,(DWORD)'p',0,scan_p)==old_proc_result);
    assert(send_key(UISET_WM_KEYUP,(DWORD)'P',0,scan_p)==old_proc_result);

    /* Focus loss clears both consumed-key and pending-character provenance;
       the subsequent key-up/character is ordinary game input. */
    reset_core(); ready_and_install();
    before_calls=call_window_proc_calls;
    assert(send_key(UISET_WM_KEYDOWN,(DWORD)'P',1,0)==0);
    assert(send_key(UISET_WM_KILLFOCUS,0,0,0)==old_proc_result);
    assert(send_key(UISET_WM_KEYUP,(DWORD)'P',0,0)==old_proc_result);
    assert(send_key(UISET_WM_CHAR,(DWORD)'P',0,0)==old_proc_result);
    assert(call_window_proc_calls==before_calls+3);

    /* The panel's S-save control can close before TranslateMessage delivers
       its activation character, so it uses the same matched-key path. */
    reset_core(); ready_and_install(); open_panel();
    assert(send_key(UISET_WM_KEYDOWN,UISET_VK_S,0,0)==0);
    ui_settings_poll(); assert(!ui_settings_is_open());
    assert(send_key(UISET_WM_KEYUP,UISET_VK_S,0,0)==0);
    assert(send_key(UISET_WM_CHAR,(DWORD)'s',0,0)==0);

    /* Alt+F4 is always forwarded, even if the user assigns that chord. */
    reset_core(); ready_and_install();
    hotkeys_clear(UIHK_OVERLAY);
    hotkeys_bind(UIHK_OVERLAY,UISET_VK_F4,UIHK_ALT);
    before_calls=call_window_proc_calls;
    assert(send_key(UISET_WM_SYSKEYDOWN,UISET_VK_F4,UIHK_ALT,
                    UISET_ALT_CONTEXT)==old_proc_result);
    assert(send_key(UISET_WM_SYSKEYUP,UISET_VK_F4,0,0)==old_proc_result);
    assert(call_window_proc_calls==before_calls+2 && !g_hotkey_queue_calls);
    puts("PASS: delayed activation chars, modifier release, focus loss, close, and Alt+F4 preserve key provenance safely");
}

static void test_draft_navigation_apply_save_close(void) {
    reset_core(); g_ui_scale_percent=150; g_ui_runtime_enabled=1; g_ui_sharp_filter=0; g_ui_keep_on_screen=1;
    ready_and_install(); open_panel();
    assert(g_ui_settings_draft_percent==150 && g_ui_settings_selected==0);
    press(UISET_VK_DOWN); assert(g_ui_settings_selected==1);
    press(UISET_VK_RIGHT); assert(!g_ui_settings_draft_enabled);
    press(UISET_VK_UP); assert(g_ui_settings_selected==0);
    press(UISET_VK_LEFT); assert(g_ui_settings_draft_percent==145);
    press(UISET_VK_RETURN);
    assert(ui_settings_is_open() && g_settings_request_valid && g_settings_request_scale==145);
    ui_settings_commit();
    assert(g_ui_scale_percent==145 && !g_ui_runtime_enabled && !g_settings_request_valid);
    ui_settings_close_panel();

    /* Saving is a render-thread mailbox action and closes only after it is
       queued; the core commit performs the actual four-key persistence. */
    open_panel(); g_ui_settings_draft_percent=175; g_ui_settings_draft_enabled=1;
    g_ui_settings_draft_crisp=1; g_ui_settings_draft_keep=0;
    press(UISET_VK_S);
    assert(!ui_settings_is_open() && g_settings_request_valid && g_settings_request_save);
    ui_settings_commit();
    assert(g_ui_scale_percent==175 && g_ui_runtime_enabled && g_ui_sharp_filter && !g_ui_keep_on_screen);
    assert(g_save_calls==4 && !strcmp(g_save_keys[0],"ScalePercent"));

    ready_and_install(); open_panel(); press(UISET_VK_ESCAPE);
    assert(!ui_settings_is_open() && !g_settings_request_valid);
    puts("PASS: render-owned four-row draft navigation, Apply, Save-and-close, and Esc close");
}

static void test_snapshot_and_latest_mailbox(void) {
    reset_core();
    g_ui_scale_percent=176; g_ui_runtime_enabled=1; g_ui_sharp_filter=0; g_ui_keep_on_screen=1;
    ui_settings_publish_snapshot();
    assert((ui_settings_snapshot_load()&UISET_PACKET_PERCENT)==176);
    assert(ui_settings_game_hwnd()==game_window);
    ui_settings_queue_values(125,1,0,1,0);
    ui_settings_queue_values(190,0,1,0,1);
    ui_settings_poll();
    assert(g_settings_request_valid && g_settings_request_scale==190);
    assert(!g_settings_request_enabled && g_settings_request_crisp && g_settings_request_save);
    g_fake_capture=1; ui_settings_commit();
    assert(g_settings_request_valid && g_ui_scale_percent==176);
    g_fake_capture=0; ui_settings_commit();
    assert(!g_settings_request_valid && g_ui_scale_percent==190 && !g_ui_runtime_enabled);
    assert(g_save_calls==4 && strstr(g_last_log,"Settings saved")!=0);
    puts("PASS: atomic snapshot and latest-wins mailbox preserve render-thread Apply/Save and capture deferral");
}

static void test_draw_surface_balance_and_geometry(void) {
    reset_core(); ready_and_install(); open_panel();
    ui_settings_draw_surface(&fake_surface);
    assert(get_dc_calls==1 && release_dc_calls==1);
    assert(save_dc_calls==1 && restore_dc_calls==1);
    assert(fill_rect_calls>=2 && first_fill_rect.left==660 && first_fill_rect.top==390);
    assert(first_fill_rect.right==1260 && first_fill_rect.bottom==690);
    assert(create_font_calls==1 && created_font_height==-18);
    assert(text_out_calls==1 && draw_text_calls>=6);
    assert(delete_object_calls>=4 && select_calls>=2);

    g_ui_screen_w=640; g_ui_screen_h=480;
    fill_rect_calls=0; memset(&first_fill_rect,0,sizeof(first_fill_rect));
    ui_settings_draw_surface(&fake_surface);
    assert(first_fill_rect.left==20 && first_fill_rect.top==90);
    assert(first_fill_rect.right==620 && first_fill_rect.bottom==390);
    assert(created_font_height==-16);
    ui_settings_close_panel();
    ui_settings_draw_surface(&fake_surface);
    assert(get_dc_calls==2);
    puts("PASS: in-game GDI panel centers within 1920x1080 and 640x480 surfaces with balanced DC/font cleanup");
}

static void test_draw_failures_close_without_trap(void) {
    reset_core(); ready_and_install(); open_panel();
    save_dc_fails=1; ui_settings_draw_surface(&fake_surface);
    assert(!ui_settings_is_open() && get_dc_calls==1 && release_dc_calls==1 && restore_dc_calls==0);
    assert(strstr(g_last_log,"overlay failed")!=0);

    reset_core(); ready_and_install(); open_panel();
    fill_rect_fail_at=1; ui_settings_draw_surface(&fake_surface);
    assert(!ui_settings_is_open() && release_dc_calls==1 && restore_dc_calls==1);

    reset_core(); ready_and_install(); open_panel();
    get_dc_fails=1; ui_settings_draw_surface(&fake_surface);
    assert(!ui_settings_is_open() && get_dc_calls==1 && release_dc_calls==0);

    reset_core(); ready_and_install(); open_panel();
    g_ui_settings_draw_text=0; ui_settings_draw_surface(&fake_surface);
    assert(!ui_settings_is_open() && release_dc_calls==0);

    reset_core(); ready_and_install(); open_panel();
    ui_settings_draw_failed();
    assert(!ui_settings_is_open() && strstr(g_last_log,"overlay failed")!=0);
    puts("PASS: every draw/API failure closes the panel and releases acquired resources so input cannot remain trapped");
}

int main(void) {
    test_parser_and_packet();
    test_game_hwnd_subclass_and_retry();
    test_deferred_open_and_key_routing();
    test_configurable_hotkey_dispatch();
    test_hotkey_provenance_and_lifecycle();
    test_draft_navigation_apply_save_close();
    test_snapshot_and_latest_mailbox();
    test_draw_surface_balance_and_geometry();
    test_draw_failures_close_without_trap();
    return 0;
}
'''


def main():
    harness = PREFIX + CORE_STUBS + CORE + '\n#include "ui_settings.h"\n' + API_STUBS + TESTS
    with tempfile.TemporaryDirectory(prefix="prm-settings-test-") as directory:
        c_file = Path(directory) / "settings_test.c"
        binary = Path(directory) / "settings_test"
        c_file.write_text(harness)
        subprocess.run([
            os.environ.get("CC", "clang"), "-m32", "-std=c11", "-O1", "-g",
            "-Wall", "-Wextra", "-Wno-unused-function", "-Wno-unused-parameter",
            "-fsanitize=address,undefined", "-fno-sanitize-recover=all",
            "-I", str(ROOT), str(c_file), "-o", str(binary),
        ], check=True)
        subprocess.run([str(binary)], check=True)


if __name__ == "__main__":
    main()
