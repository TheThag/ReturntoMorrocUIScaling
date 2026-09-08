#ifndef PRM_UI_SETTINGS_H
#define PRM_UI_SETTINGS_H

/*
 * Small native settings window for the proxy.  This header is included once,
 * late in prm_uifix.c, after the freestanding types, helpers and globals have
 * been declared.  It deliberately does not include a Windows header or call
 * an imported API.
 *
 * The window thread only owns the controls and its message loop.  It reads
 * the current values when the window is shown, then publishes one packed
 * request at a time.  The render thread consumes that request in
 * ui_settings_poll() and calls the callback supplied by prm_uifix.c.
 */

#ifndef UI_SETTINGS_APPLY
#define UI_SETTINGS_APPLY ui_settings_apply
#endif

#define UISET_THREAD_NEVER    0
#define UISET_THREAD_STARTING 1
#define UISET_THREAD_RUNNING  2
#define UISET_THREAD_FAILED   3

#define UISET_PACKET_VALID    0x80000000UL
#define UISET_PACKET_ENABLED  0x00000100UL
#define UISET_PACKET_CRISP    0x00000200UL
#define UISET_PACKET_KEEP     0x00000400UL
#define UISET_PACKET_SAVE     0x00000800UL
#define UISET_PACKET_PERCENT  0x000000ffUL

#define UISET_ID_PERCENT  1001
#define UISET_ID_MINUS   1002
#define UISET_ID_PLUS    1003
#define UISET_ID_ENABLED 1004
#define UISET_ID_CRISP   1005
#define UISET_ID_KEEP    1006
#define UISET_ID_APPLY   1007
#define UISET_ID_SAVE    1008
#define UISET_ID_CLOSE   1009
#define UISET_ID_STATUS  1010

#define UISET_CLASS_NAME "PRM_UI_FIX_SETTINGS"
#define UISET_VK_ESCAPE 0x1b
#define UISET_VK_F2     0x71
#define UISET_IDC_ARROW 32512UL
#define UISET_KEY_REPEAT 0x40000000UL

#define UISET_WM_CREATE     0x0001UL
#define UISET_WM_DESTROY    0x0002UL
#define UISET_WM_CLOSE      0x0010UL
#define UISET_WM_KEYDOWN    0x0100UL
#define UISET_WM_SYSKEYDOWN 0x0104UL
#define UISET_WM_COMMAND    0x0111UL
#define UISET_WM_NCDESTROY  0x0082UL
#define UISET_WM_APP_SHOW   0x8041UL
#define UISET_WM_APP_TOGGLE 0x8042UL

#define UISET_BN_CLICKED    0
#define UISET_BM_GETCHECK   0x00f0UL
#define UISET_BM_SETCHECK   0x00f1UL
#define UISET_BST_UNCHECKED 0
#define UISET_BST_CHECKED   1

#define UISET_SW_HIDE       0
#define UISET_SW_SHOW       5

#define UISET_WS_OVERLAPPED  0x00000000UL
#define UISET_WS_CAPTION     0x00c00000UL
#define UISET_WS_SYSMENU     0x00080000UL
#define UISET_WS_CHILD       0x40000000UL
#define UISET_WS_VISIBLE     0x10000000UL
#define UISET_WS_TABSTOP     0x00010000UL
#define UISET_WS_BORDER      0x00800000UL
#define UISET_WS_EX_TOOLWINDOW 0x00000080UL
#define UISET_WS_EX_CONTROLPARENT 0x00010000UL
#define UISET_ES_NUMBER      0x00002000UL
#define UISET_BS_PUSHBUTTON  0x00000000UL
#define UISET_BS_AUTOCHECKBOX 0x00000003UL
#define UISET_CLIENT_WIDTH   360
#define UISET_CLIENT_HEIGHT  230
#define UISET_FALLBACK_WIDTH 380
#define UISET_FALLBACK_HEIGHT 280

typedef LONG UISettingsLResult;
typedef ULONG_PTR UISettingsWParam;
typedef LONG UISettingsLParam;
typedef UISettingsLResult (WINAPI *UISettingsWndProc)(HWND, DWORD, UISettingsWParam, UISettingsLParam);
typedef DWORD (WINAPI *UISettingsThreadProc)(LPVOID);

typedef struct {
    UINT style;
    UISettingsWndProc lpfnWndProc;
    int cbClsExtra;
    int cbWndExtra;
    HINSTANCE hInstance;
    HANDLE hIcon;
    HANDLE hCursor;
    HANDLE hbrBackground;
    LPCSTR lpszMenuName;
    LPCSTR lpszClassName;
} UISettingsWndClassA;

typedef struct {
    HWND hwnd;
    DWORD message;
    UISettingsWParam wParam;
    UISettingsLParam lParam;
    DWORD time;
    POINT pt;
    DWORD lPrivate;
} UISettingsMsg;

#if defined(__i386__) || defined(_M_IX86)
_Static_assert(sizeof(UISettingsMsg) == 32, "PRM settings MSG must match MSG32");
_Static_assert(sizeof(UISettingsWndClassA) == 40, "PRM settings WNDCLASS must match WNDCLASS32");
#endif

typedef WORD (WINAPI *PFN_UISettingsRegisterClassA)(const UISettingsWndClassA*);
typedef HWND (WINAPI *PFN_UISettingsCreateWindowExA)(DWORD, LPCSTR, LPCSTR, DWORD,
                                                     int, int, int, int, HWND, HANDLE,
                                                     HINSTANCE, LPVOID);
typedef BOOL (WINAPI *PFN_UISettingsGetMessageA)(UISettingsMsg*, HWND, UINT, UINT);
typedef BOOL (WINAPI *PFN_UISettingsTranslateMessage)(const UISettingsMsg*);
typedef UISettingsLResult (WINAPI *PFN_UISettingsDispatchMessageA)(const UISettingsMsg*);
typedef UISettingsLResult (WINAPI *PFN_UISettingsDefWindowProcA)(HWND, DWORD,
                                                                  UISettingsWParam,
                                                                  UISettingsLParam);
typedef BOOL (WINAPI *PFN_UISettingsShowWindow)(HWND, int);
typedef BOOL (WINAPI *PFN_UISettingsUpdateWindow)(HWND);
typedef BOOL (WINAPI *PFN_UISettingsSetWindowTextA)(HWND, LPCSTR);
typedef int (WINAPI *PFN_UISettingsGetWindowTextA)(HWND, LPSTR, int);
typedef UISettingsLResult (WINAPI *PFN_UISettingsSendMessageA)(HWND, DWORD,
                                                               UISettingsWParam,
                                                               UISettingsLParam);
typedef HWND (WINAPI *PFN_UISettingsSetFocus)(HWND);
typedef BOOL (WINAPI *PFN_UISettingsSetForegroundWindow)(HWND);
typedef HWND (WINAPI *PFN_UISettingsGetForegroundWindow)(void);
typedef BOOL (WINAPI *PFN_UISettingsPostMessageA)(HWND, DWORD, UISettingsWParam,
                                                   UISettingsLParam);
typedef HANDLE (WINAPI *PFN_UISettingsLoadCursorA)(HINSTANCE, LPCSTR);
typedef BOOL (WINAPI *PFN_UISettingsIsDialogMessageA)(HWND, UISettingsMsg*);
typedef BOOL (WINAPI *PFN_UISettingsAdjustWindowRectEx)(RECT*, DWORD, BOOL, DWORD);
typedef BOOL (WINAPI *PFN_UISettingsGetWindowRect)(HWND, RECT*);
typedef HANDLE (WINAPI *PFN_UISettingsCreateThread)(LPVOID, SIZE_T,
                                                     UISettingsThreadProc, LPVOID,
                                                     DWORD, DWORD*);

static volatile LONG g_ui_settings_api_state;
static volatile LONG g_ui_settings_thread_state;
static volatile LONG g_ui_settings_open_request;
static volatile LONG g_ui_settings_visible;
static volatile LONG g_ui_settings_f2_latched;
static volatile DWORD g_ui_settings_mailbox;
static volatile DWORD g_ui_settings_snapshot;
static volatile DWORD g_ui_settings_game_hwnd_snapshot;
static HWND g_ui_settings_window;
static HWND g_ui_settings_percent;
static HWND g_ui_settings_minus;
static HWND g_ui_settings_plus;
static HWND g_ui_settings_enabled;
static HWND g_ui_settings_crisp;
static HWND g_ui_settings_keep;
static HWND g_ui_settings_status;
static DWORD g_ui_settings_thread_id;

static PFN_UISettingsRegisterClassA g_ui_settings_register_class;
static PFN_UISettingsCreateWindowExA g_ui_settings_create_window;
static PFN_UISettingsGetMessageA g_ui_settings_get_message;
static PFN_UISettingsTranslateMessage g_ui_settings_translate_message;
static PFN_UISettingsDispatchMessageA g_ui_settings_dispatch_message;
static PFN_UISettingsDefWindowProcA g_ui_settings_def_window_proc;
static PFN_UISettingsShowWindow g_ui_settings_show_window;
static PFN_UISettingsUpdateWindow g_ui_settings_update_window;
static PFN_UISettingsSetWindowTextA g_ui_settings_set_window_text;
static PFN_UISettingsGetWindowTextA g_ui_settings_get_window_text;
static PFN_UISettingsSendMessageA g_ui_settings_send_message;
static PFN_UISettingsSetFocus g_ui_settings_set_focus;
static PFN_UISettingsSetForegroundWindow g_ui_settings_set_foreground;
static PFN_UISettingsGetForegroundWindow g_ui_settings_get_foreground;
static PFN_UISettingsPostMessageA g_ui_settings_post_message;
static PFN_UISettingsLoadCursorA g_ui_settings_load_cursor;
static PFN_UISettingsIsDialogMessageA g_ui_settings_is_dialog_message;
static PFN_UISettingsAdjustWindowRectEx g_ui_settings_adjust_window_rect;
static PFN_UISettingsGetWindowRect g_ui_settings_get_window_rect;
static PFN_UISettingsCreateThread g_ui_settings_create_thread;

static DWORD WINAPI ui_settings_thread_proc(LPVOID unused);

static int ui_settings_clamp_percent(int percent) {
    if (percent < 100) return 100;
    if (percent > 200) return 200;
    return percent;
}

static DWORD ui_settings_pack(int percent, int enabled, int crisp, int keep, int save) {
    DWORD packet = UISET_PACKET_VALID | (DWORD)ui_settings_clamp_percent(percent);
    if (enabled) packet |= UISET_PACKET_ENABLED;
    if (crisp) packet |= UISET_PACKET_CRISP;
    if (keep) packet |= UISET_PACKET_KEEP;
    if (save) packet |= UISET_PACKET_SAVE;
    return packet;
}

static DWORD ui_settings_snapshot_load(void) {
    return __atomic_load_n(&g_ui_settings_snapshot, __ATOMIC_ACQUIRE);
}

/* The settings window is a separate thread. Publish the game HWND from the
 * render/input side, where g_input_hwnd is owned, and let the window thread
 * consume only this atomic snapshot. Prefer the immutable native main-window
 * slot; the input hook is only a render-thread fallback for early/unknown
 * builds. */
static void ui_settings_publish_game_hwnd(void) {
    HMODULE base = g_exe;
    HWND hwnd = 0;
    if (base && g_exe_size >= PRM_MAIN_HWND_RVA + sizeof(HWND) &&
        mem_readable((BYTE*)base + PRM_MAIN_HWND_RVA, sizeof(HWND)))
        hwnd = *(HWND*)((BYTE*)base + PRM_MAIN_HWND_RVA);
    if (!hwnd) hwnd = g_input_hwnd;
    __atomic_store_n(&g_ui_settings_game_hwnd_snapshot,
                     (DWORD)(ULONG_PTR)hwnd, __ATOMIC_RELEASE);
}

/* Called on the render thread. The root present boundary also calls this
 * after ui_settings_commit(), since commit follows the normal poll call. */
static void ui_settings_publish_snapshot(void) {
    DWORD packet = ui_settings_pack(g_ui_scale_percent,
                                    g_ui_runtime_enabled,
                                    g_ui_sharp_filter,
                                    g_ui_keep_on_screen, 0);
    __atomic_store_n(&g_ui_settings_snapshot, packet, __ATOMIC_RELEASE);
    ui_settings_publish_game_hwnd();
}

static int ui_settings_parse_percent(const char* text, int* out) {
    unsigned int i = 0;
    int value = 0;
    int digits = 0;
    if (!text || !out) return 0;
    while (text[i] == ' ' || text[i] == '\t') ++i;
    while (text[i] >= '0' && text[i] <= '9') {
        if (value > 1000) return 0;
        value = value * 10 + (text[i] - '0');
        digits = 1;
        ++i;
    }
    while (text[i] == ' ' || text[i] == '\t') ++i;
    if (!digits || text[i]) return 0;
    if (value < 100 || value > 200) return 0;
    *out = value;
    return 1;
}

static void ui_settings_resolve_apis(void) {
    LONG expected = 0;
    HMODULE u32;
    HMODULE k32;
    if (!__atomic_compare_exchange_n(&g_ui_settings_api_state, &expected, 1, 0,
                                     __ATOMIC_ACQ_REL, __ATOMIC_ACQUIRE)) return;
    u32 = find_loaded_module("user32.dll");
    k32 = find_loaded_module("kernel32.dll");
    if (u32) {
        if (!g_GetAsyncKeyState)
            g_GetAsyncKeyState = (PFN_GetAsyncKeyState)resolve_export(u32, "GetAsyncKeyState");
        g_ui_settings_register_class = (PFN_UISettingsRegisterClassA)resolve_export(u32, "RegisterClassA");
        g_ui_settings_create_window = (PFN_UISettingsCreateWindowExA)resolve_export(u32, "CreateWindowExA");
        g_ui_settings_get_message = (PFN_UISettingsGetMessageA)resolve_export(u32, "GetMessageA");
        g_ui_settings_translate_message = (PFN_UISettingsTranslateMessage)resolve_export(u32, "TranslateMessage");
        g_ui_settings_dispatch_message = (PFN_UISettingsDispatchMessageA)resolve_export(u32, "DispatchMessageA");
        g_ui_settings_def_window_proc = (PFN_UISettingsDefWindowProcA)resolve_export(u32, "DefWindowProcA");
        g_ui_settings_show_window = (PFN_UISettingsShowWindow)resolve_export(u32, "ShowWindow");
        g_ui_settings_update_window = (PFN_UISettingsUpdateWindow)resolve_export(u32, "UpdateWindow");
        g_ui_settings_set_window_text = (PFN_UISettingsSetWindowTextA)resolve_export(u32, "SetWindowTextA");
        g_ui_settings_get_window_text = (PFN_UISettingsGetWindowTextA)resolve_export(u32, "GetWindowTextA");
        g_ui_settings_send_message = (PFN_UISettingsSendMessageA)resolve_export(u32, "SendMessageA");
        g_ui_settings_set_focus = (PFN_UISettingsSetFocus)resolve_export(u32, "SetFocus");
        g_ui_settings_set_foreground = (PFN_UISettingsSetForegroundWindow)resolve_export(u32, "SetForegroundWindow");
        g_ui_settings_get_foreground = (PFN_UISettingsGetForegroundWindow)resolve_export(u32, "GetForegroundWindow");
        g_ui_settings_post_message = (PFN_UISettingsPostMessageA)resolve_export(u32, "PostMessageA");
        g_ui_settings_load_cursor = (PFN_UISettingsLoadCursorA)resolve_export(u32, "LoadCursorA");
        g_ui_settings_is_dialog_message = (PFN_UISettingsIsDialogMessageA)resolve_export(u32, "IsDialogMessageA");
        g_ui_settings_adjust_window_rect = (PFN_UISettingsAdjustWindowRectEx)resolve_export(u32, "AdjustWindowRectEx");
        g_ui_settings_get_window_rect = (PFN_UISettingsGetWindowRect)resolve_export(u32, "GetWindowRect");
    }
    if (k32)
        g_ui_settings_create_thread = (PFN_UISettingsCreateThread)resolve_export(k32, "CreateThread");
    __atomic_store_n(&g_ui_settings_api_state, 2, __ATOMIC_RELEASE);
}

static HWND ui_settings_window_load(void) {
    return (HWND)__atomic_load_n((void* volatile*)&g_ui_settings_window, __ATOMIC_ACQUIRE);
}

static void ui_settings_window_store(HWND hwnd) {
    __atomic_store_n((void* volatile*)&g_ui_settings_window, (void*)hwnd, __ATOMIC_RELEASE);
}

static HWND ui_settings_game_hwnd(void) {
    return (HWND)(ULONG_PTR)__atomic_load_n(&g_ui_settings_game_hwnd_snapshot,
                                             __ATOMIC_ACQUIRE);
}

static void ui_settings_set_status(const char* text) {
    HWND status = g_ui_settings_status;
    if (status && g_ui_settings_set_window_text) g_ui_settings_set_window_text(status, text);
}

static int ui_settings_current_percent(void) {
    DWORD snapshot = ui_settings_snapshot_load();
    if (!(snapshot & UISET_PACKET_VALID)) return 133;
    return ui_settings_clamp_percent((int)(snapshot & UISET_PACKET_PERCENT));
}

static void ui_settings_set_check(HWND control, int checked) {
    if (control && g_ui_settings_send_message)
        g_ui_settings_send_message(control, UISET_BM_SETCHECK,
                                   (UISettingsWParam)(checked ? UISET_BST_CHECKED : UISET_BST_UNCHECKED), 0);
}

static int ui_settings_get_check(HWND control) {
    if (!control || !g_ui_settings_send_message) return 0;
    return g_ui_settings_send_message(control, UISET_BM_GETCHECK, 0, 0) == UISET_BST_CHECKED;
}

static void ui_settings_sync_controls(void) {
    char value[16];
    DWORD snapshot = ui_settings_snapshot_load();
    int percent = 133;
    int enabled = 1;
    int crisp = 0;
    int keep = 1;
    unsigned int i = 0;
    if (snapshot & UISET_PACKET_VALID) {
        percent = ui_settings_clamp_percent((int)(snapshot & UISET_PACKET_PERCENT));
        enabled = (snapshot & UISET_PACKET_ENABLED) != 0;
        crisp = (snapshot & UISET_PACKET_CRISP) != 0;
        keep = (snapshot & UISET_PACKET_KEEP) != 0;
    }
    if (g_ui_settings_set_window_text && g_ui_settings_percent) {
        if (percent >= 100) value[i++] = (char)('0' + percent / 100);
        value[i++] = (char)('0' + (percent / 10) % 10);
        value[i++] = (char)('0' + percent % 10);
        value[i] = 0;
        g_ui_settings_set_window_text(g_ui_settings_percent, value);
    }
    ui_settings_set_check(g_ui_settings_enabled, enabled);
    ui_settings_set_check(g_ui_settings_crisp, crisp);
    ui_settings_set_check(g_ui_settings_keep, keep);
}

static HWND ui_settings_make_control(LPCSTR class_name, LPCSTR text, DWORD style,
                                      int x, int y, int width, int height, DWORD id) {
    HWND parent = ui_settings_window_load();
    if (!g_ui_settings_create_window || !parent) return 0;
    return g_ui_settings_create_window(0, class_name, text,
        UISET_WS_CHILD | UISET_WS_VISIBLE | style, x, y, width, height,
        parent, (HANDLE)(ULONG_PTR)id, (HINSTANCE)g_self, 0);
}

static void ui_settings_create_controls(HWND hwnd) {
    if (!hwnd || !g_ui_settings_create_window) return;
    ui_settings_window_store(hwnd);
    ui_settings_make_control("STATIC", "Scale percent (100-200):", 0, 14, 15, 190, 20, 0);
    g_ui_settings_percent = ui_settings_make_control("EDIT", "133",
        UISET_WS_BORDER | UISET_WS_TABSTOP | UISET_ES_NUMBER, 210, 12, 60, 22,
        UISET_ID_PERCENT);
    g_ui_settings_minus = ui_settings_make_control("BUTTON", "-", UISET_BS_PUSHBUTTON,
        278, 12, 28, 22, UISET_ID_MINUS);
    g_ui_settings_plus = ui_settings_make_control("BUTTON", "+", UISET_BS_PUSHBUTTON,
        310, 12, 28, 22, UISET_ID_PLUS);
    ui_settings_make_control("STATIC", "Options:", 0, 14, 49, 70, 18, 0);
    g_ui_settings_enabled = ui_settings_make_control("BUTTON", "Enable UI scaling",
        UISET_BS_AUTOCHECKBOX | UISET_WS_TABSTOP, 25, 70, 310, 22, UISET_ID_ENABLED);
    g_ui_settings_crisp = ui_settings_make_control("BUTTON", "Crisp filtering",
        UISET_BS_AUTOCHECKBOX | UISET_WS_TABSTOP, 25, 96, 310, 22, UISET_ID_CRISP);
    g_ui_settings_keep = ui_settings_make_control("BUTTON", "Keep on screen",
        UISET_BS_AUTOCHECKBOX | UISET_WS_TABSTOP, 25, 122, 310, 22, UISET_ID_KEEP);
    g_ui_settings_status = ui_settings_make_control("STATIC", "Changes apply while the game runs.",
        0, 14, 153, 320, 20, UISET_ID_STATUS);
    ui_settings_make_control("BUTTON", "Apply", UISET_BS_PUSHBUTTON | UISET_WS_TABSTOP,
        84, 185, 72, 26, UISET_ID_APPLY);
    ui_settings_make_control("BUTTON", "Save", UISET_BS_PUSHBUTTON | UISET_WS_TABSTOP,
        164, 185, 72, 26, UISET_ID_SAVE);
    ui_settings_make_control("BUTTON", "Close", UISET_BS_PUSHBUTTON | UISET_WS_TABSTOP,
        244, 185, 72, 26, UISET_ID_CLOSE);
    ui_settings_sync_controls();
}

static void ui_settings_close_window(void) {
    HWND hwnd = ui_settings_window_load();
    HWND game;
    __atomic_store_n(&g_ui_settings_open_request, 0, __ATOMIC_RELEASE);
    __atomic_store_n(&g_ui_settings_visible, 0, __ATOMIC_RELEASE);
    /* The render poll may still see F2 held after this UI-thread close. */
    __atomic_store_n(&g_ui_settings_f2_latched, 1, __ATOMIC_RELEASE);
    if (hwnd && g_ui_settings_show_window) g_ui_settings_show_window(hwnd, UISET_SW_HIDE);
    game = ui_settings_game_hwnd();
    /* The game window belongs to the game thread. SetFocus requires the
     * target to share the caller's input queue, so activation is handed back
     * with SetForegroundWindow and the native WM_ACTIVATE path restores focus. */
    if (game && g_ui_settings_set_foreground) g_ui_settings_set_foreground(game);
}

static void ui_settings_show_window(void) {
    HWND hwnd = ui_settings_window_load();
    if (!hwnd) return;
    ui_settings_sync_controls();
    __atomic_store_n(&g_ui_settings_open_request, 0, __ATOMIC_RELEASE);
    __atomic_store_n(&g_ui_settings_visible, 1, __ATOMIC_RELEASE);
    if (g_ui_settings_show_window) g_ui_settings_show_window(hwnd, UISET_SW_SHOW);
    if (g_ui_settings_update_window) g_ui_settings_update_window(hwnd);
    if (g_ui_settings_set_foreground) g_ui_settings_set_foreground(hwnd);
    if (g_ui_settings_set_focus && g_ui_settings_percent) g_ui_settings_set_focus(g_ui_settings_percent);
}

static void ui_settings_close_if_visible(void) {
    if (__atomic_load_n(&g_ui_settings_visible, __ATOMIC_ACQUIRE))
        ui_settings_close_window();
}

static void ui_settings_post_window(DWORD message) {
    HWND hwnd = ui_settings_window_load();
    if (hwnd && g_ui_settings_post_message)
        g_ui_settings_post_message(hwnd, message, 0, 0);
}

static void ui_settings_request_open(void) {
    LONG state;
    LONG expected;
    HWND hwnd;
    __atomic_store_n(&g_ui_settings_open_request, 1, __ATOMIC_RELEASE);
    state = __atomic_load_n(&g_ui_settings_thread_state, __ATOMIC_ACQUIRE);
    if (state == UISET_THREAD_FAILED) return;
    hwnd = ui_settings_window_load();
    if (state == UISET_THREAD_RUNNING) {
        if (hwnd) ui_settings_post_window(UISET_WM_APP_SHOW);
        return;
    }
    if (state == UISET_THREAD_STARTING) return;
    expected = UISET_THREAD_NEVER;
    if (!__atomic_compare_exchange_n(&g_ui_settings_thread_state, &expected,
                                     UISET_THREAD_STARTING, 0, __ATOMIC_ACQ_REL,
                                     __ATOMIC_ACQUIRE)) return;
    if (!g_ui_settings_create_thread) {
        __atomic_store_n(&g_ui_settings_thread_state, UISET_THREAD_FAILED, __ATOMIC_RELEASE);
        return;
    }
    g_ui_settings_thread_id = 0;
    {
        HANDLE thread_handle = g_ui_settings_create_thread(0, 0,
            (UISettingsThreadProc)ui_settings_thread_proc, 0, 0,
            &g_ui_settings_thread_id);
        if (!thread_handle) {
            __atomic_store_n(&g_ui_settings_thread_state, UISET_THREAD_FAILED, __ATOMIC_RELEASE);
        } else if (g_CloseHandle) {
            g_CloseHandle(thread_handle);
        }
    }
}

static void ui_settings_queue_values(int percent, int enabled, int crisp, int keep, int save) {
    DWORD packet = ui_settings_pack(percent, enabled, crisp, keep, save);
    __atomic_store_n(&g_ui_settings_mailbox, packet, __ATOMIC_RELEASE);
}

static int ui_settings_read_percent(int* out) {
    char text[24];
    int n;
    unsigned int i;
    if (!out || !g_ui_settings_percent || !g_ui_settings_get_window_text) return 0;
    for (i = 0; i < sizeof(text); ++i) text[i] = 0;
    n = g_ui_settings_get_window_text(g_ui_settings_percent, text, sizeof(text));
    if (n < 0 || n >= (int)sizeof(text)) return 0;
    return ui_settings_parse_percent(text, out);
}

static void ui_settings_set_percent_control(int percent) {
    char text[16];
    unsigned int i = 0;
    percent = ui_settings_clamp_percent(percent);
    if (!g_ui_settings_percent || !g_ui_settings_set_window_text) return;
    if (percent >= 100) text[i++] = (char)('0' + percent / 100);
    text[i++] = (char)('0' + (percent / 10) % 10);
    text[i++] = (char)('0' + percent % 10);
    text[i] = 0;
    g_ui_settings_set_window_text(g_ui_settings_percent, text);
}

static void ui_settings_step_percent(int delta) {
    int percent;
    if (!ui_settings_read_percent(&percent)) percent = ui_settings_current_percent();
    ui_settings_set_percent_control(percent + delta);
}

static void ui_settings_queue_controls(int save) {
    int percent;
    if (!ui_settings_read_percent(&percent)) {
        ui_settings_set_status("Scale must be between 100 and 200.");
        return;
    }
    if (!g_ui_settings_enabled || !g_ui_settings_crisp || !g_ui_settings_keep ||
        !g_ui_settings_send_message) {
        ui_settings_set_status("Settings controls are unavailable.");
        return;
    }
    ui_settings_queue_values(percent,
        ui_settings_get_check(g_ui_settings_enabled),
        ui_settings_get_check(g_ui_settings_crisp),
        ui_settings_get_check(g_ui_settings_keep), save);
    (void)save;
    ui_settings_set_status("Changes apply while the game runs.");
}

static UISettingsLResult WINAPI ui_settings_wndproc(HWND hwnd, DWORD message,
                                                     UISettingsWParam wParam,
                                                     UISettingsLParam lParam) {
    DWORD id;
    DWORD code;
    (void)lParam;
    switch (message) {
    case UISET_WM_CREATE:
        ui_settings_create_controls(hwnd);
        return 0;
    case UISET_WM_COMMAND:
        id = (DWORD)(wParam & 0xffffUL);
        code = (DWORD)((wParam >> 16) & 0xffffUL);
        if (code != UISET_BN_CLICKED) return 0;
        if (id == UISET_ID_MINUS) ui_settings_step_percent(-1);
        else if (id == UISET_ID_PLUS) ui_settings_step_percent(1);
        else if (id == UISET_ID_APPLY) ui_settings_queue_controls(0);
        else if (id == UISET_ID_SAVE) ui_settings_queue_controls(1);
        else if (id == UISET_ID_CLOSE) ui_settings_close_window();
        return 0;
    case UISET_WM_CLOSE:
        ui_settings_close_window();
        return 0;
    case UISET_WM_NCDESTROY:
        __atomic_store_n(&g_ui_settings_visible, 0, __ATOMIC_RELEASE);
        if (ui_settings_window_load() == hwnd) ui_settings_window_store(0);
        break;
    case UISET_WM_APP_SHOW:
        ui_settings_show_window();
        return 0;
    case UISET_WM_APP_TOGGLE:
        /* A toggle can be queued before a close message reaches this thread.
         * Treat it as the render-side close command so stale messages cannot
         * reopen a window that the user just hid. */
        ui_settings_close_if_visible();
        return 0;
    default:
        break;
    }
    return g_ui_settings_def_window_proc ?
        g_ui_settings_def_window_proc(hwnd, message, wParam, lParam) : 0;
}

static DWORD WINAPI ui_settings_thread_proc(LPVOID unused) {
    UISettingsWndClassA cls;
    UISettingsMsg msg;
    HWND owner;
    HWND hwnd;
    HINSTANCE instance;
    RECT desired;
    RECT owner_rect;
    DWORD window_style;
    DWORD window_ex_style;
    int x;
    int y;
    int width;
    int height;
    (void)unused;
    if (!g_ui_settings_register_class || !g_ui_settings_create_window ||
        !g_ui_settings_get_message || !g_ui_settings_translate_message ||
        !g_ui_settings_dispatch_message || !g_ui_settings_show_window ||
        !g_ui_settings_is_dialog_message) {
        __atomic_store_n(&g_ui_settings_thread_state, UISET_THREAD_FAILED, __ATOMIC_RELEASE);
        return 0;
    }
    owner = ui_settings_game_hwnd();
    if (!owner) {
        __atomic_store_n(&g_ui_settings_thread_state, UISET_THREAD_FAILED, __ATOMIC_RELEASE);
        return 0;
    }
    instance = (HINSTANCE)g_self;
    if (!instance && g_GetModuleHandleA) instance = (HINSTANCE)g_GetModuleHandleA(0);
    cls.style = 0;
    cls.lpfnWndProc = ui_settings_wndproc;
    cls.cbClsExtra = 0;
    cls.cbWndExtra = 0;
    cls.hInstance = instance;
    cls.hIcon = 0;
    cls.hbrBackground = (HANDLE)(ULONG_PTR)16; /* COLOR_BTNFACE + 1 */
    cls.hCursor = g_ui_settings_load_cursor ?
        g_ui_settings_load_cursor(0, (LPCSTR)(ULONG_PTR)UISET_IDC_ARROW) : 0;
    cls.lpszMenuName = 0;
    cls.lpszClassName = UISET_CLASS_NAME;
    if (!g_ui_settings_register_class(&cls)) {
        __atomic_store_n(&g_ui_settings_thread_state, UISET_THREAD_FAILED, __ATOMIC_RELEASE);
        return 0;
    }
    window_style = UISET_WS_OVERLAPPED | UISET_WS_CAPTION | UISET_WS_SYSMENU;
    window_ex_style = UISET_WS_EX_TOOLWINDOW | UISET_WS_EX_CONTROLPARENT;
    desired.left = 0;
    desired.top = 0;
    desired.right = UISET_CLIENT_WIDTH;
    desired.bottom = UISET_CLIENT_HEIGHT;
    width = UISET_FALLBACK_WIDTH;
    height = UISET_FALLBACK_HEIGHT;
    if (g_ui_settings_adjust_window_rect &&
        g_ui_settings_adjust_window_rect(&desired, window_style, 0, window_ex_style) &&
        desired.right > desired.left && desired.bottom > desired.top) {
        width = (int)(desired.right - desired.left);
        height = (int)(desired.bottom - desired.top);
    }
    x = 160;
    y = 120;
    if (g_ui_settings_get_window_rect && g_ui_settings_get_window_rect(owner, &owner_rect) &&
        owner_rect.right > owner_rect.left && owner_rect.bottom > owner_rect.top) {
        x = (int)(owner_rect.left +
                  ((owner_rect.right - owner_rect.left) - width) / 2);
        y = (int)(owner_rect.top +
                  ((owner_rect.bottom - owner_rect.top) - height) / 2);
    }
    hwnd = g_ui_settings_create_window(window_ex_style,
        UISET_CLASS_NAME, "PRM UI FIX Settings", window_style,
        x, y, width, height, owner, 0, instance, 0);
    if (!hwnd) {
        __atomic_store_n(&g_ui_settings_thread_state, UISET_THREAD_FAILED, __ATOMIC_RELEASE);
        return 0;
    }
    ui_settings_window_store(hwnd);
    __atomic_store_n(&g_ui_settings_thread_state, UISET_THREAD_RUNNING, __ATOMIC_RELEASE);
    if (__atomic_load_n(&g_ui_settings_open_request, __ATOMIC_ACQUIRE)) ui_settings_show_window();
    for (;;) {
        BOOL got = g_ui_settings_get_message(&msg, 0, 0, 0);
        if (got <= 0) break;
        if ((msg.message == UISET_WM_KEYDOWN || msg.message == UISET_WM_SYSKEYDOWN) &&
            (msg.wParam == UISET_VK_ESCAPE || msg.wParam == UISET_VK_F2)) {
            if (msg.wParam != UISET_VK_F2 || !(msg.lParam & UISET_KEY_REPEAT))
                ui_settings_close_window();
            continue;
        }
        if (g_ui_settings_is_dialog_message &&
            g_ui_settings_is_dialog_message(hwnd, &msg)) continue;
        g_ui_settings_translate_message(&msg);
        g_ui_settings_dispatch_message(&msg);
    }
    __atomic_store_n(&g_ui_settings_visible, 0, __ATOMIC_RELEASE);
    ui_settings_window_store(0);
    __atomic_store_n(&g_ui_settings_thread_state, UISET_THREAD_FAILED, __ATOMIC_RELEASE);
    return 0;
}

/* Called by the render/present path.  The UI thread never calls this. */
static void ui_settings_poll(void) {
    DWORD packet;
    short key_state;
    int key_down;
    int key_pressed;
    ui_settings_publish_snapshot();
    packet = __atomic_exchange_n(&g_ui_settings_mailbox, 0, __ATOMIC_ACQ_REL);
    if (packet & UISET_PACKET_VALID) {
        UI_SETTINGS_APPLY((int)(packet & UISET_PACKET_PERCENT),
                          (packet & UISET_PACKET_ENABLED) != 0,
                          (packet & UISET_PACKET_CRISP) != 0,
                          (packet & UISET_PACKET_KEEP) != 0,
                          (packet & UISET_PACKET_SAVE) != 0);
    }
    ui_settings_resolve_apis();
    if (!g_GetAsyncKeyState) return;
    key_state = g_GetAsyncKeyState(UISET_VK_F2);
    key_down = (key_state & 0x8000) != 0;
    key_pressed = key_down &&
        !__atomic_load_n(&g_ui_settings_f2_latched, __ATOMIC_ACQUIRE);
    __atomic_store_n(&g_ui_settings_f2_latched, key_down ? 1 : 0, __ATOMIC_RELEASE);
    if (!key_pressed || !g_ui_settings_get_foreground) return;
    if (g_ui_settings_get_foreground() != ui_settings_game_hwnd()) return;
    if (__atomic_load_n(&g_ui_settings_visible, __ATOMIC_ACQUIRE))
        ui_settings_post_window(UISET_WM_APP_TOGGLE);
    else
        ui_settings_request_open();
}

#endif /* PRM_UI_SETTINGS_H */
