#!/usr/bin/env python3
"""Exercise the native F2 settings mailbox and render-thread commit contract.

The settings header is compiled in a 32-bit host fixture with fake Win32
functions.  The fixture also extracts the production callback/commit pair so
that capture deferral, live updates, and four-key Save persistence are tested
without launching Wine or touching a real INI file.
"""

import os
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parent


def extract_function(source, name):
    marker = f"static "
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
typedef void *HWND;
typedef int BOOL;
typedef struct { LONG x,y; } POINT;
typedef struct { LONG left,top,right,bottom; } RECT;
#define WINAPI __attribute__((stdcall))
#define PRM_MAIN_HWND_RVA 0x00D0AABCUL
#define PRM_UI_CAPTURE_RVA 0x00AB786CUL
typedef short (WINAPI *PFN_GetAsyncKeyState)(int);
typedef HMODULE (WINAPI *PFN_GetModuleHandleA)(LPCSTR);
typedef BOOL (WINAPI *PFN_CloseHandle)(HANDLE);
static HMODULE g_self;
static HMODULE g_exe;
static DWORD g_exe_size;
static char g_ini_path[520] = "fixture.ini";
static HWND g_input_hwnd;
static PFN_GetAsyncKeyState g_GetAsyncKeyState;
static PFN_GetModuleHandleA g_GetModuleHandleA;
static PFN_CloseHandle g_CloseHandle;
static int g_ui_scale_percent=133;
static int g_ui_enabled=1;
static int g_ui_runtime_enabled=1;
static int g_ui_sharp_filter=0;
static int g_ui_keep_on_screen=1;
static int g_owner_bitmap_hooks_installed=1;
static DWORD g_fake_capture;
static int g_log_count;
static char g_last_log[160];
static int g_save_calls;
static int g_save_fail_at;
static char g_save_keys[4][32];
static char g_save_values[4][32];
static BOOL WINAPI fake_write_profile(LPCSTR, LPCSTR, LPCSTR, LPCSTR);

static int mem_readable(const void *p, DWORD bytes) {
    (void)p; (void)bytes; return 1;
}
static HMODULE find_loaded_module(const char *name) {
    (void)name; return (HMODULE)(ULONG_PTR)0x12340000UL;
}
static void *resolve_export(HMODULE module, const char *name) {
    (void)module;
    if (!strcmp(name,"WritePrivateProfileStringA")) return (void*)fake_write_profile;
    return 0;
}
static void s_append(char *dst, unsigned int cap, const char *src) {
    unsigned int i=0,j=0;
    if (!dst || !cap || !src) return;
    while (i+1<cap && dst[i]) ++i;
    while (i+1<cap && src[j]) dst[i++]=src[j++];
    if (i<cap) dst[i]=0;
}
static void s_append_uint(char *dst, unsigned int cap, DWORD value) {
    char temp[16]; unsigned int n=0;
    if (!value) { s_append(dst,cap,"0"); return; }
    while (value && n<sizeof(temp)) { temp[n++]=(char)('0'+value%10); value/=10; }
    while (n) { char one[2]={temp[--n],0}; s_append(dst,cap,one); }
}
static void log_line(const char *line) {
    ++g_log_count;
    s_append(g_last_log,sizeof(g_last_log),line);
}
static DWORD WINAPI fake_capture_thread(void *unused) {
    (void)unused; return g_fake_capture;
}
'''


CORE_STUBS = r'''
static int g_settings_request_valid,g_settings_request_scale,g_settings_request_enabled;
static int g_settings_request_crisp,g_settings_request_keep,g_settings_request_save;
static DWORD owner_native_capture(void) { return g_fake_capture; }
'''


API_STUBS = r'''
static HWND game_window=(HWND)(ULONG_PTR)0x1010;
static HWND overlay_window=(HWND)(ULONG_PTR)0x2020;
static HWND foreground_window;
static short key_state;
static int create_thread_calls;
static int create_thread_fails;
static int run_thread_proc;
static int close_handle_calls;
static int post_calls;
static DWORD last_post_message;
static int show_calls;
static int last_show_mode=-1;
static int set_foreground_calls;
static int set_focus_calls;
static int cross_thread_focus_calls;
static HWND last_foreground;
static HWND last_focus;
static int register_calls;
static int top_create_calls;
static int child_create_calls;
static int child_bounds_bad;
static int dispatch_calls;
static int translate_calls;
static int dialog_calls;
static int thread_message_mode;
static int thread_message_step;
static char last_percent_text[24];
static int checkbox_enabled_state;
static int checkbox_crisp_state;
static int checkbox_keep_state;
static int mutate_settings_after_percent;
static char registered_class[64];
static char created_class[64];

static WORD WINAPI fake_register_class(const UISettingsWndClassA *cls) {
    assert(cls && cls->lpfnWndProc==ui_settings_wndproc);
    assert(cls->hbrBackground==(HANDLE)(ULONG_PTR)16);
    assert(cls->hCursor==(HANDLE)(ULONG_PTR)0x9090);
    ++register_calls;
    strncpy(registered_class,cls->lpszClassName,sizeof(registered_class)-1);
    return 1;
}
static HWND WINAPI fake_create_window(DWORD ex, LPCSTR class_name, LPCSTR title,
                                      DWORD style, int x, int y, int width, int height,
                                      HWND parent, HANDLE menu, HINSTANCE instance,
                                      LPVOID param) {
    (void)title; (void)style; (void)menu; (void)instance; (void)param;
    if (!strcmp(class_name,UISET_CLASS_NAME)) {
        assert(ex==(UISET_WS_EX_TOOLWINDOW|UISET_WS_EX_CONTROLPARENT));
        assert(parent==game_window);
        ++top_create_calls;
        strncpy(created_class,class_name,sizeof(created_class)-1);
        assert(width==UISET_FALLBACK_WIDTH && height==UISET_FALLBACK_HEIGHT);
        ui_settings_wndproc(overlay_window,UISET_WM_CREATE,0,0);
        return overlay_window;
    }
    ++child_create_calls;
    if (x<0 || y<0 || width<=0 || height<=0 ||
        x+width>UISET_CLIENT_WIDTH || y+height>UISET_CLIENT_HEIGHT) child_bounds_bad=1;
    return (HWND)(ULONG_PTR)(0x3000UL+(DWORD)child_create_calls);
}
static BOOL WINAPI fake_get_message(UISettingsMsg *msg, HWND filter, UINT first, UINT last) {
    int step=thread_message_step++;
    (void)filter; (void)first; (void)last;
    memset(msg,0,sizeof(*msg));
    if (thread_message_mode==1 && step==1) {
        msg->hwnd=overlay_window; msg->message=UISET_WM_KEYDOWN;
        msg->wParam=UISET_VK_F2; msg->lParam=UISET_KEY_REPEAT; return 1;
    }
    if (step != 0) return 0;
    msg->hwnd=overlay_window;
    if (thread_message_mode==0) msg->message=UISET_WM_CLOSE;
    else if (thread_message_mode==1) {
        msg->message=UISET_WM_KEYDOWN; msg->wParam=UISET_VK_F2; msg->lParam=0;
    } else if (thread_message_mode==2) {
        msg->message=UISET_WM_KEYDOWN; msg->wParam=UISET_VK_ESCAPE; msg->lParam=0;
    } else {
        msg->message=UISET_WM_KEYDOWN; msg->wParam=0x09; msg->lParam=0;
    }
    return 1;
}
static BOOL WINAPI fake_translate(const UISettingsMsg *msg) {
    (void)msg; ++translate_calls; return 1;
}
static UISettingsLResult WINAPI fake_dispatch(const UISettingsMsg *msg) {
    ++dispatch_calls;
    return ui_settings_wndproc(msg->hwnd,msg->message,msg->wParam,msg->lParam);
}
static BOOL WINAPI fake_dialog(HWND hwnd, UISettingsMsg *msg) {
    (void)hwnd; ++dialog_calls;
    return msg && msg->message==UISET_WM_KEYDOWN && msg->wParam==0x09;
}
static BOOL WINAPI fake_adjust(RECT *rect, DWORD style, BOOL menu, DWORD ex) {
    (void)style; (void)menu; (void)ex;
    assert(rect->right==UISET_CLIENT_WIDTH && rect->bottom==UISET_CLIENT_HEIGHT);
    rect->right=UISET_FALLBACK_WIDTH; rect->bottom=UISET_FALLBACK_HEIGHT; return 1;
}
static BOOL WINAPI fake_get_window_rect(HWND hwnd, RECT *rect) {
    assert(hwnd==game_window); rect->left=0; rect->top=0; rect->right=1920; rect->bottom=1080; return 1;
}
static HANDLE WINAPI fake_load_cursor(HINSTANCE instance, LPCSTR resource) {
    assert(instance==0 && (ULONG_PTR)resource==UISET_IDC_ARROW); return (HANDLE)(ULONG_PTR)0x9090;
}
static BOOL WINAPI fake_update(HWND hwnd) { assert(hwnd==overlay_window); return 1; }
static BOOL WINAPI fake_set_text(HWND hwnd, LPCSTR text) {
    if (hwnd==g_ui_settings_percent) {
        strncpy(last_percent_text,text,sizeof(last_percent_text)-1);
        last_percent_text[sizeof(last_percent_text)-1]=0;
        if (mutate_settings_after_percent) {
            g_ui_runtime_enabled=0; g_ui_sharp_filter=1; g_ui_keep_on_screen=0;
        }
    }
    return 1;
}
static int WINAPI fake_get_text(HWND hwnd, LPSTR text, int cap) {
    (void)hwnd; if (cap>0) { strncpy(text,"133",(size_t)cap-1); text[cap-1]=0; } return 3;
}
static UISettingsLResult WINAPI fake_send(HWND hwnd, DWORD message, UISettingsWParam wp, UISettingsLParam lp) {
    int checked=(wp==UISET_BST_CHECKED);
    (void)lp;
    if (message==UISET_BM_SETCHECK) {
        if (hwnd==g_ui_settings_enabled) checkbox_enabled_state=checked;
        else if (hwnd==g_ui_settings_crisp) checkbox_crisp_state=checked;
        else if (hwnd==g_ui_settings_keep) checkbox_keep_state=checked;
        return 0;
    }
    if (message==UISET_BM_GETCHECK) {
        if (hwnd==g_ui_settings_enabled) return checkbox_enabled_state ? UISET_BST_CHECKED : UISET_BST_UNCHECKED;
        if (hwnd==g_ui_settings_crisp) return checkbox_crisp_state ? UISET_BST_CHECKED : UISET_BST_UNCHECKED;
        if (hwnd==g_ui_settings_keep) return checkbox_keep_state ? UISET_BST_CHECKED : UISET_BST_UNCHECKED;
    }
    return UISET_BST_UNCHECKED;
}
static BOOL WINAPI fake_close_handle(HANDLE handle) {
    assert(handle==(HANDLE)(ULONG_PTR)0x3030); ++close_handle_calls; return 1;
}
static HANDLE WINAPI fake_create_thread(void *security, SIZE_T stack, UISettingsThreadProc proc,
                                        void *arg, DWORD flags, DWORD *tid) {
    (void)security; (void)stack; (void)flags;
    ++create_thread_calls;
    if (tid) *tid=77;
    if (create_thread_fails) return 0;
    if (run_thread_proc) proc(arg);
    return (HANDLE)(ULONG_PTR)0x3030;
}
static short WINAPI fake_async(int key) {
    assert(key==UISET_VK_F2); return key_state;
}
static HWND WINAPI fake_foreground(void) { return foreground_window; }
static BOOL WINAPI fake_post(HWND hwnd, DWORD message, UISettingsWParam wp, UISettingsLParam lp) {
    (void)hwnd; (void)wp; (void)lp; ++post_calls; last_post_message=message; return 1;
}
static BOOL WINAPI fake_show(HWND hwnd, int mode) {
    assert(hwnd==overlay_window); ++show_calls; last_show_mode=mode; return 1;
}
static BOOL WINAPI fake_set_foreground(HWND hwnd) {
    ++set_foreground_calls; last_foreground=hwnd; foreground_window=hwnd; return 1;
}
static HWND WINAPI fake_set_focus(HWND hwnd) {
    ++set_focus_calls; last_focus=hwnd;
    if (hwnd==game_window) ++cross_thread_focus_calls;
    return hwnd;
}
static BOOL WINAPI fake_write_profile(LPCSTR section, LPCSTR key, LPCSTR value, LPCSTR path) {
    assert(!strcmp(section,"UI")); assert(!strcmp(path,"fixture.ini"));
    assert(g_save_calls<4);
    strncpy(g_save_keys[g_save_calls],key,sizeof(g_save_keys[0])-1);
    strncpy(g_save_values[g_save_calls],value,sizeof(g_save_values[0])-1);
    if (g_save_fail_at==g_save_calls) { ++g_save_calls; return 0; }
    ++g_save_calls; return 1;
}
static void reset_fake_apis(void) {
    foreground_window=game_window; key_state=0;
    create_thread_calls=0; create_thread_fails=0; run_thread_proc=0; close_handle_calls=0;
    post_calls=0;
    last_post_message=0; show_calls=0; last_show_mode=-1;
    set_foreground_calls=0; set_focus_calls=0; cross_thread_focus_calls=0;
    last_foreground=0; last_focus=0;
    register_calls=0; top_create_calls=0; child_create_calls=0; child_bounds_bad=0;
    dispatch_calls=0; translate_calls=0; dialog_calls=0;
    thread_message_mode=0; thread_message_step=0;
    last_percent_text[0]=0;
    checkbox_enabled_state=0; checkbox_crisp_state=0; checkbox_keep_state=0;
    mutate_settings_after_percent=0;
    registered_class[0]=0; created_class[0]=0;
    g_ui_settings_api_state=2;
    g_ui_settings_f2_latched=0;
    g_GetAsyncKeyState=fake_async;
    g_CloseHandle=fake_close_handle;
    g_ui_settings_register_class=fake_register_class;
    g_ui_settings_create_window=fake_create_window;
    g_ui_settings_get_message=fake_get_message;
    g_ui_settings_translate_message=fake_translate;
    g_ui_settings_dispatch_message=fake_dispatch;
    g_ui_settings_def_window_proc=0;
    g_ui_settings_load_cursor=fake_load_cursor;
    g_ui_settings_is_dialog_message=fake_dialog;
    g_ui_settings_adjust_window_rect=fake_adjust;
    g_ui_settings_get_window_rect=fake_get_window_rect;
    g_ui_settings_get_foreground=fake_foreground;
    g_ui_settings_create_thread=fake_create_thread;
    g_ui_settings_post_message=fake_post;
    g_ui_settings_show_window=fake_show;
    g_ui_settings_update_window=fake_update;
    g_ui_settings_set_window_text=fake_set_text;
    g_ui_settings_get_window_text=fake_get_text;
    g_ui_settings_send_message=fake_send;
    g_ui_settings_set_foreground=fake_set_foreground;
    g_ui_settings_set_focus=fake_set_focus;
    g_input_hwnd=game_window;
}
static void reset_core(void) {
    g_settings_request_valid=0;
    g_settings_request_scale=0; g_settings_request_enabled=0;
    g_settings_request_crisp=0; g_settings_request_keep=0; g_settings_request_save=0;
    g_ui_scale_percent=133; g_ui_enabled=1; g_ui_runtime_enabled=1;
    g_ui_sharp_filter=0; g_ui_keep_on_screen=1;
    g_owner_bitmap_hooks_installed=1; g_fake_capture=0;
    g_exe=0; g_exe_size=0;
    g_log_count=0; g_last_log[0]=0;
    g_save_calls=0; g_save_fail_at=-1;
    memset(g_save_keys,0,sizeof(g_save_keys)); memset(g_save_values,0,sizeof(g_save_values));
    g_ui_settings_thread_state=UISET_THREAD_NEVER;
    g_ui_settings_open_request=0; g_ui_settings_visible=0;
    g_ui_settings_f2_latched=0; g_ui_settings_mailbox=0;
    g_ui_settings_snapshot=0; g_ui_settings_game_hwnd_snapshot=0;
    ui_settings_window_store(0); g_ui_settings_percent=0;
    g_ui_settings_enabled=0; g_ui_settings_crisp=0; g_ui_settings_keep=0;
    g_ui_settings_status=0;
}
'''


TESTS = r'''
static void test_parser_and_packet(void) {
    int value=0;
    assert(ui_settings_parse_percent("100",&value) && value==100);
    assert(ui_settings_parse_percent(" 200 ",&value) && value==200);
    assert(!ui_settings_parse_percent("99",&value));
    assert(!ui_settings_parse_percent("201",&value));
    assert(!ui_settings_parse_percent("",&value));
    assert(!ui_settings_parse_percent("133x",&value));
    assert((ui_settings_pack(50,1,0,1,1) & UISET_PACKET_PERCENT)==100);
    assert((ui_settings_pack(250,0,1,0,0) & UISET_PACKET_PERCENT)==200);
    assert((ui_settings_pack(150,1,0,1,1) & UISET_PACKET_ENABLED)!=0);
    assert((ui_settings_pack(150,1,0,1,1) & UISET_PACKET_CRISP)==0);
    assert((ui_settings_pack(150,1,0,1,1) & UISET_PACKET_KEEP)!=0);
    assert((ui_settings_pack(150,1,0,1,1) & UISET_PACKET_SAVE)!=0);
    puts("PASS: settings percent validation, clamp and packed command fields");
}

static void test_latest_mailbox_and_deferred_commit(void) {
    reset_core(); reset_fake_apis();
    ui_settings_queue_values(125,1,0,1,0);
    ui_settings_queue_values(175,0,1,0,0); /* Latest request wins. */
    ui_settings_poll();
    assert((ui_settings_snapshot_load() & UISET_PACKET_PERCENT)==133);
    assert(ui_settings_game_hwnd()==game_window);
    assert(g_settings_request_valid && g_settings_request_scale==175);
    assert(!g_settings_request_enabled && g_settings_request_crisp && !g_settings_request_keep);
    assert(g_ui_scale_percent==133 && g_ui_runtime_enabled==1 && !g_ui_sharp_filter);
    assert(g_save_calls==0);
    g_fake_capture=1;
    ui_settings_commit();
    assert(g_settings_request_valid && g_ui_scale_percent==133);
    g_fake_capture=0;
    ui_settings_commit();
    assert(!g_settings_request_valid && g_ui_scale_percent==175);
    assert(!g_ui_runtime_enabled && g_ui_sharp_filter && !g_ui_keep_on_screen);
    ui_settings_poll();
    assert(g_settings_request_valid==0);
    puts("PASS: latest settings mailbox wins and commit defers during native capture");
}

static void test_save_and_partial_failure(void) {
    reset_core(); reset_fake_apis();
    ui_settings_queue_values(190,1,0,1,1);
    ui_settings_poll(); ui_settings_commit();
    assert(g_ui_scale_percent==190 && g_ui_runtime_enabled && !g_ui_sharp_filter && g_ui_keep_on_screen);
    assert(g_save_calls==4);
    assert(!strcmp(g_save_keys[0],"ScalePercent") && !strcmp(g_save_values[0],"190"));
    assert(!strcmp(g_save_keys[1],"Enabled") && !strcmp(g_save_values[1],"1"));
    assert(!strcmp(g_save_keys[2],"SharpFilter") && !strcmp(g_save_values[2],"0"));
    assert(!strcmp(g_save_keys[3],"KeepOnScreen") && !strcmp(g_save_values[3],"1"));
    assert(strstr(g_last_log,"saved")!=0);

    reset_core(); reset_fake_apis(); g_save_fail_at=2;
    ui_settings_queue_values(160,0,1,0,1);
    ui_settings_poll(); ui_settings_commit();
    assert(g_save_calls==4 && g_ui_scale_percent==160 && !g_ui_runtime_enabled);
    assert(strstr(g_last_log,"save failed")!=0);
    puts("PASS: Apply performs no INI writes; Save writes four UI keys and reports partial failure");
}

static void test_snapshot_is_coherent(void) {
    reset_core(); reset_fake_apis();
    g_ui_scale_percent=176; g_ui_runtime_enabled=1;
    g_ui_sharp_filter=0; g_ui_keep_on_screen=1;
    g_ui_settings_percent=(HWND)(ULONG_PTR)0x3101;
    g_ui_settings_enabled=(HWND)(ULONG_PTR)0x3102;
    g_ui_settings_crisp=(HWND)(ULONG_PTR)0x3103;
    g_ui_settings_keep=(HWND)(ULONG_PTR)0x3104;
    ui_settings_publish_snapshot();
    g_input_hwnd=(HWND)(ULONG_PTR)0x9999;
    assert(ui_settings_game_hwnd()==game_window);

    /* A raw read after the first control update would observe these changes;
     * one atomic snapshot must keep all four controls on the old values. */
    mutate_settings_after_percent=1;
    ui_settings_sync_controls();
    assert(!strcmp(last_percent_text,"176"));
    assert(checkbox_enabled_state==1 && checkbox_crisp_state==0 && checkbox_keep_state==1);
    puts("PASS: settings controls use one coherent atomic snapshot");
}

static void test_f2_foreground_and_lifecycle(void) {
    reset_core(); reset_fake_apis();
    g_ui_settings_thread_state=UISET_THREAD_NEVER;
    foreground_window=(HWND)(ULONG_PTR)0x9999; key_state=0x8000;
    ui_settings_poll();
    assert(create_thread_calls==0 && g_ui_settings_thread_state==UISET_THREAD_NEVER);

    foreground_window=game_window; key_state=0x8000;
    ui_settings_poll();
    assert(create_thread_calls==0); /* A held key pressed outside the game stays consumed. */
    key_state=0; ui_settings_poll();
    key_state=0x8000; create_thread_fails=1;
    ui_settings_poll();
    assert(create_thread_calls==1 && g_ui_settings_thread_state==UISET_THREAD_FAILED);
    key_state=0; ui_settings_poll();
    key_state=0x8000; ui_settings_poll();
    assert(create_thread_calls==1); /* Failed creation is latched; no retry loop. */

    reset_fake_apis(); g_ui_settings_thread_state=UISET_THREAD_NEVER;
    g_ui_settings_open_request=0; g_ui_settings_visible=0; ui_settings_window_store(0);
    key_state=0x8000; ui_settings_poll();
    assert(create_thread_calls==1 && g_ui_settings_thread_state==UISET_THREAD_STARTING);
    key_state=0x8000; ui_settings_poll();
    assert(create_thread_calls==1); /* Starting thread owns the pending open request. */

    ui_settings_window_store(overlay_window); g_ui_settings_visible=1;
    key_state=0; ui_settings_poll();
    key_state=0x8000; ui_settings_poll();
    assert(post_calls==1 && last_post_message==UISET_WM_APP_TOGGLE);

    g_ui_settings_open_request=1; g_ui_settings_visible=1;
    ui_settings_close_window();
    assert(!g_ui_settings_open_request && !g_ui_settings_visible);
    assert(show_calls==1 && last_show_mode==UISET_SW_HIDE);
    assert(set_foreground_calls==1 && last_foreground==game_window);
    assert(set_focus_calls==0 && cross_thread_focus_calls==0);
    assert(g_ui_settings_f2_latched==1);
    ui_settings_wndproc(overlay_window,UISET_WM_APP_TOGGLE,0,0);
    assert(!g_ui_settings_visible && show_calls==1 && last_show_mode==UISET_SW_HIDE);
    key_state=0; ui_settings_poll();
    key_state=0x8000; ui_settings_poll();
    assert(post_calls==1); /* Closing does not immediately reopen on the held key. */
    puts("PASS: F2 uses foreground-gated edges, idempotent close, and native focus handoff");
}

static void test_full_thread_creation_and_messages(void) {
    reset_core(); reset_fake_apis();
    run_thread_proc=1; thread_message_mode=0;
    g_ui_settings_open_request=1;
    ui_settings_publish_snapshot();
    ui_settings_request_open();
    assert(create_thread_calls==1 && close_handle_calls==1);
    assert(register_calls==1 && top_create_calls==1 && child_create_calls==12);
    assert(!strcmp(registered_class,UISET_CLASS_NAME));
    assert(!strcmp(created_class,UISET_CLASS_NAME));
    assert(!strcmp(registered_class,created_class));
    assert(!child_bounds_bad);
    assert(dispatch_calls==1 && translate_calls==1 && dialog_calls==1);
    assert(show_calls==2 && last_show_mode==UISET_SW_HIDE);
    assert(set_foreground_calls==2 && set_focus_calls==1);
    assert(last_foreground==game_window && last_focus!=game_window);
    assert(cross_thread_focus_calls==0);
    assert(g_ui_settings_thread_state==UISET_THREAD_FAILED && !ui_settings_window_load());

    reset_core(); reset_fake_apis();
    run_thread_proc=1; thread_message_mode=1; g_ui_settings_open_request=1;
    ui_settings_publish_snapshot();
    ui_settings_request_open();
    assert(!strcmp(registered_class,created_class));
    assert(show_calls==2 && set_foreground_calls==2 && set_focus_calls==1);
    assert(last_foreground==game_window && last_focus!=game_window);
    assert(cross_thread_focus_calls==0);
    assert(!dispatch_calls && !translate_calls && !dialog_calls);
    assert(close_handle_calls==1);

    reset_core(); reset_fake_apis();
    run_thread_proc=1; thread_message_mode=2; g_ui_settings_open_request=1;
    ui_settings_publish_snapshot();
    ui_settings_request_open();
    assert(show_calls==2 && set_foreground_calls==2 && set_focus_calls==1);
    assert(last_foreground==game_window && last_focus!=game_window);
    assert(cross_thread_focus_calls==0);
    assert(!dispatch_calls && !translate_calls);

    reset_core(); reset_fake_apis();
    run_thread_proc=1; thread_message_mode=3; g_ui_settings_open_request=1;
    ui_settings_publish_snapshot();
    ui_settings_request_open();
    assert(dialog_calls==1 && !dispatch_calls && !translate_calls);
    puts("PASS: thread startup uses one shared class, creates in-range controls, closes its handle, and handles close/F2/Esc/dialog messages");
}

int main(void) {
    test_parser_and_packet();
    test_latest_mailbox_and_deferred_commit();
    test_save_and_partial_failure();
    test_snapshot_is_coherent();
    test_f2_foreground_and_lifecycle();
    test_full_thread_creation_and_messages();
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
