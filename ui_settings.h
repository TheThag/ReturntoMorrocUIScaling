#ifndef PRM_UI_SETTINGS_H
#define PRM_UI_SETTINGS_H

/*
 * Render-thread settings panel.
 *
 * The configurable overlay binding is handled by a lightweight subclass of
 * the game's main window.  The subclass only places bits in atomic mailboxes;
 * it never creates a window, changes focus, calls the settings callback, or
 * touches the UI globals.  The render thread owns the draft values, drains
 * those mailboxes, and paints the panel into the DirectDraw surface supplied
 * by the present hook.
 */

#ifndef UI_SETTINGS_APPLY
#define UI_SETTINGS_APPLY ui_settings_apply
#endif

#define UISET_PACKET_VALID    0x80000000UL
#define UISET_PACKET_ENABLED  0x00000100UL
#define UISET_PACKET_CRISP    0x00000200UL
#define UISET_PACKET_KEEP     0x00000400UL
#define UISET_PACKET_SAVE     0x00000800UL
#define UISET_PACKET_PERCENT  0x000000ffUL

#define UISET_EVENT_TOGGLE    0x00000001UL
#define UISET_EVENT_UP        0x00000002UL
#define UISET_EVENT_DOWN      0x00000004UL
#define UISET_EVENT_LEFT      0x00000008UL
#define UISET_EVENT_RIGHT     0x00000010UL
#define UISET_EVENT_ENTER     0x00000020UL
#define UISET_EVENT_SAVE      0x00000040UL
#define UISET_EVENT_ESCAPE    0x00000080UL

#define UISET_VK_ESCAPE       0x1bUL
#define UISET_VK_BACK         0x08UL
#define UISET_VK_TAB          0x09UL
#define UISET_VK_RETURN       0x0dUL
#define UISET_VK_SPACE        0x20UL
#define UISET_VK_F4           0x73UL
#define UISET_VK_S            0x53UL
#define UISET_VK_UP           0x26UL
#define UISET_VK_DOWN         0x28UL
#define UISET_VK_LEFT         0x25UL
#define UISET_VK_RIGHT        0x27UL
#define UISET_KEY_REPEAT      0x40000000UL
#define UISET_ALT_CONTEXT     0x20000000UL

#define UISET_WM_KEYDOWN      0x0100UL
#define UISET_WM_KEYUP        0x0101UL
#define UISET_WM_CHAR         0x0102UL
#define UISET_WM_SYSKEYDOWN   0x0104UL
#define UISET_WM_SYSKEYUP     0x0105UL
#define UISET_WM_SYSCHAR      0x0106UL
#define UISET_WM_NCDESTROY    0x0082UL
#define UISET_WM_KILLFOCUS    0x0008UL
#define UISET_WM_ACTIVATEAPP  0x001cUL
#define UISET_WM_LBUTTONDOWN  0x0201UL
#define UISET_WM_LBUTTONUP    0x0202UL
#define UISET_WM_LBUTTONDBLCLK 0x0203UL
#define UISET_WM_RBUTTONDOWN  0x0204UL
#define UISET_WM_RBUTTONUP    0x0205UL
#define UISET_WM_RBUTTONDBLCLK 0x0206UL
#define UISET_WM_MBUTTONDOWN  0x0207UL
#define UISET_WM_MBUTTONUP    0x0208UL
#define UISET_WM_MBUTTONDBLCLK 0x0209UL
#define UISET_WM_MOUSEWHEEL   0x020aUL
#define UISET_WM_XBUTTONDOWN  0x020bUL
#define UISET_WM_XBUTTONUP    0x020cUL
#define UISET_WM_XBUTTONDBLCLK 0x020dUL
#define UISET_WM_MOUSEHWHEEL  0x020eUL

#define UISET_GWL_WNDPROC     (-4)
#define UISET_CLIENT_MARGIN   24
#define UISET_PANEL_WIDTH     600
#define UISET_PANEL_HEIGHT    300
#define UISET_PANEL_MIN_EDGE  16
#define UISET_FONT_MIN        16
#define UISET_FONT_MAX        28
#define UISET_FW_NORMAL       400
#define UISET_DEFAULT_CHARSET 1UL
#define UISET_OUT_DEFAULT     0UL
#define UISET_CLIP_DEFAULT    0UL
#define UISET_DEFAULT_QUALITY 0UL
#define UISET_DEFAULT_PITCH   0UL
#define UISET_FF_DONTCARE     0UL
#define UISET_TRANSPARENT     1
#define UISET_DT_SINGLELINE   0x0020UL
#define UISET_DT_VCENTER      0x0004UL
#define UISET_DT_LEFT         0x0000UL

/* ui_hotkeys.h is included by the production translation unit before this
 * header.  These fallback indices keep the settings fixture self-contained;
 * the real header supplies the same public contract. */
#ifndef UIHK_OVERLAY
#define UIHK_OVERLAY          0
#endif
#ifndef UIHK_SHIFT
#define UIHK_SHIFT            1UL
#define UIHK_CTRL             2UL
#define UIHK_ALT              4UL
#define UIHK_WIN              8UL
#endif

typedef LONG UISettingsLResult;
typedef ULONG_PTR UISettingsWParam;
typedef LONG UISettingsLParam;
typedef UISettingsLResult (WINAPI *UISettingsWndProc)(HWND, DWORD,
                                                       UISettingsWParam,
                                                       UISettingsLParam);

typedef LONG (WINAPI *PFN_UISettingsSetWindowLongA)(HWND, int, LONG);
typedef UISettingsLResult (WINAPI *PFN_UISettingsCallWindowProcA)(UISettingsWndProc,
                                                                   HWND, DWORD,
                                                                   UISettingsWParam,
                                                                   UISettingsLParam);
typedef HRESULT (WINAPI *PFN_UISettingsGetDC)(void*, void**);
typedef HRESULT (WINAPI *PFN_UISettingsReleaseDC)(void*, void*);
typedef int (WINAPI *PFN_UISettingsSaveDC)(void*);
typedef BOOL (WINAPI *PFN_UISettingsRestoreDC)(void*, int);
typedef void* (WINAPI *PFN_UISettingsCreateSolidBrush)(DWORD);
typedef int (WINAPI *PFN_UISettingsFillRect)(void*, const RECT*, void*);
typedef BOOL (WINAPI *PFN_UISettingsDeleteObject)(void*);
typedef void* (WINAPI *PFN_UISettingsSelectObject)(void*, void*);
typedef int (WINAPI *PFN_UISettingsSetBkMode)(void*, int);
typedef DWORD (WINAPI *PFN_UISettingsSetTextColor)(void*, DWORD);
typedef BOOL (WINAPI *PFN_UISettingsTextOutA)(void*, int, int, LPCSTR, int);
typedef int (WINAPI *PFN_UISettingsDrawTextA)(void*, LPCSTR, int, RECT*, UINT);
typedef void* (WINAPI *PFN_UISettingsCreateFontA)(int, int, int, int, int,
                                                  DWORD, DWORD, DWORD, DWORD,
                                                  DWORD, DWORD, DWORD, DWORD,
                                                  LPCSTR);

static volatile LONG g_ui_settings_api_state;
static volatile LONG g_ui_settings_subclass_state;
static volatile LONG g_ui_settings_panel_open;
static volatile LONG g_ui_settings_deferred_open;
static volatile DWORD g_ui_settings_events;
static volatile DWORD g_ui_settings_mailbox;
static volatile DWORD g_ui_settings_snapshot;
static volatile DWORD g_ui_settings_game_hwnd_snapshot;
static UISettingsWndProc g_ui_settings_original_wndproc;
static HWND g_ui_settings_bound_hwnd;
static int g_ui_settings_selected;
static int g_ui_settings_draft_percent;
static int g_ui_settings_draft_enabled;
static int g_ui_settings_draft_crisp;
static int g_ui_settings_draft_keep;
static int g_ui_settings_status;
static int g_ui_settings_failure_logged;

#define UISET_PENDING_CHAR_CAP 8
typedef struct UISettingsPendingChar {
    BYTE vk;
    BYTE scan;
    BYTE extended;
    BYTE expected;
} UISettingsPendingChar;
static BYTE g_ui_settings_consumed_keys[256];
static UISettingsPendingChar g_ui_settings_pending_chars[UISET_PENDING_CHAR_CAP];
static unsigned int g_ui_settings_pending_char_count;

static PFN_UISettingsSetWindowLongA g_ui_settings_set_window_long;
static PFN_UISettingsCallWindowProcA g_ui_settings_call_window_proc;
static PFN_UISettingsGetDC g_ui_settings_get_dc;
static PFN_UISettingsReleaseDC g_ui_settings_release_dc;
static PFN_UISettingsSaveDC g_ui_settings_save_dc;
static PFN_UISettingsRestoreDC g_ui_settings_restore_dc;
static PFN_UISettingsCreateSolidBrush g_ui_settings_create_brush;
static PFN_UISettingsFillRect g_ui_settings_fill_rect;
static PFN_UISettingsDeleteObject g_ui_settings_delete_object;
static PFN_UISettingsSelectObject g_ui_settings_select_object;
static PFN_UISettingsSetBkMode g_ui_settings_set_bk_mode;
static PFN_UISettingsSetTextColor g_ui_settings_set_text_color;
static PFN_UISettingsTextOutA g_ui_settings_text_out;
static PFN_UISettingsDrawTextA g_ui_settings_draw_text;
static PFN_UISettingsCreateFontA g_ui_settings_create_font;

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

static HWND ui_settings_game_hwnd(void) {
    HWND hwnd = 0;
    if (g_exe && g_exe_size >= PRM_MAIN_HWND_RVA + sizeof(HWND) &&
        mem_readable((BYTE*)g_exe + PRM_MAIN_HWND_RVA, sizeof(HWND)))
        hwnd = *(HWND*)((BYTE*)g_exe + PRM_MAIN_HWND_RVA);
    if (!hwnd) hwnd = g_input_hwnd;
    __atomic_store_n(&g_ui_settings_game_hwnd_snapshot,
                     (DWORD)(ULONG_PTR)hwnd, __ATOMIC_RELEASE);
    return hwnd;
}

static void ui_settings_publish_snapshot(void) {
    DWORD packet = ui_settings_pack(g_ui_scale_percent,
                                    g_ui_runtime_enabled,
                                    g_ui_sharp_filter,
                                    g_ui_keep_on_screen, 0);
    __atomic_store_n(&g_ui_settings_snapshot, packet, __ATOMIC_RELEASE);
    ui_settings_game_hwnd();
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
    if (!digits || text[i] || value < 100 || value > 200) return 0;
    *out = value;
    return 1;
}

static void ui_settings_resolve_apis(void) {
    LONG expected = 0;
    HMODULE u32, g32;
    if (!__atomic_compare_exchange_n(&g_ui_settings_api_state, &expected, 1, 0,
                                     __ATOMIC_ACQ_REL, __ATOMIC_ACQUIRE)) return;
    u32 = find_loaded_module("user32.dll");
    g32 = find_loaded_module("gdi32.dll");
    if (u32) {
        g_ui_settings_set_window_long =
            (PFN_UISettingsSetWindowLongA)resolve_export(u32, "SetWindowLongA");
        g_ui_settings_call_window_proc =
            (PFN_UISettingsCallWindowProcA)resolve_export(u32, "CallWindowProcA");
        g_ui_settings_fill_rect =
            (PFN_UISettingsFillRect)resolve_export(u32, "FillRect");
        g_ui_settings_draw_text =
            (PFN_UISettingsDrawTextA)resolve_export(u32, "DrawTextA");
    }
    if (g32) {
        g_ui_settings_save_dc =
            (PFN_UISettingsSaveDC)resolve_export(g32, "SaveDC");
        g_ui_settings_restore_dc =
            (PFN_UISettingsRestoreDC)resolve_export(g32, "RestoreDC");
        g_ui_settings_create_brush =
            (PFN_UISettingsCreateSolidBrush)resolve_export(g32, "CreateSolidBrush");
        g_ui_settings_delete_object =
            (PFN_UISettingsDeleteObject)resolve_export(g32, "DeleteObject");
        g_ui_settings_select_object =
            (PFN_UISettingsSelectObject)resolve_export(g32, "SelectObject");
        g_ui_settings_set_bk_mode =
            (PFN_UISettingsSetBkMode)resolve_export(g32, "SetBkMode");
        g_ui_settings_set_text_color =
            (PFN_UISettingsSetTextColor)resolve_export(g32, "SetTextColor");
        g_ui_settings_text_out =
            (PFN_UISettingsTextOutA)resolve_export(g32, "TextOutA");
        g_ui_settings_create_font =
            (PFN_UISettingsCreateFontA)resolve_export(g32, "CreateFontA");
    }
    __atomic_store_n(&g_ui_settings_api_state, 2, __ATOMIC_RELEASE);
}

static void ui_settings_queue_values(int percent, int enabled, int crisp,
                                      int keep, int save) {
    __atomic_store_n(&g_ui_settings_mailbox,
                     ui_settings_pack(percent, enabled, crisp, keep, save),
                     __ATOMIC_RELEASE);
}

static void ui_settings_fail_close(void) {
    __atomic_store_n(&g_ui_settings_panel_open, 0, __ATOMIC_RELEASE);
    __atomic_store_n(&g_ui_settings_deferred_open, 0, __ATOMIC_RELEASE);
    g_ui_settings_status = 3;
    if (!g_ui_settings_failure_logged) {
        log_line("Settings overlay failed; closed");
        g_ui_settings_failure_logged = 1;
    }
}

static UISettingsLResult ui_settings_forward(HWND hwnd, DWORD message,
                                              UISettingsWParam wParam,
                                              UISettingsLParam lParam) {
    if (g_ui_settings_original_wndproc && g_ui_settings_call_window_proc)
        return g_ui_settings_call_window_proc(g_ui_settings_original_wndproc,
                                              hwnd, message, wParam, lParam);
    return 0;
}

static void ui_settings_event(DWORD event) {
    __atomic_fetch_or(&g_ui_settings_events, event, __ATOMIC_RELEASE);
}

static DWORD ui_settings_hotkey_bit(unsigned int action) {
    if (action >= 32U) return 0;
    return 1UL << action;
}

static int ui_settings_key_is_printable(DWORD vk, DWORD mods, BYTE* expected) {
    /* The pending-character filter is intentionally narrow.  It covers the
       ASCII key names accepted by the INI parser without ever swallowing an
       unrelated Unicode/IME character after a blank binding. */
    if (vk >= (DWORD)'A' && vk <= (DWORD)'Z') {
        if (expected) {
            *expected = (BYTE)(mods & UIHK_CTRL ? (vk & 0x1fUL) : vk);
            if (!(mods & UIHK_CTRL) && !(mods & UIHK_SHIFT))
                *expected = (BYTE)(vk + ((DWORD)'a' - (DWORD)'A'));
        }
        return 1;
    }
    if (vk >= (DWORD)'0' && vk <= (DWORD)'9') {
        if (expected) {
            static const char shifted[] = ")!@#$%^&*(";
            *expected = (BYTE)(mods & UIHK_CTRL ? (vk & 0x1fUL) : vk);
            if (mods & UIHK_SHIFT)
                *expected = (BYTE)shifted[vk - (DWORD)'0'];
        }
        return 1;
    }
    if (vk == UISET_VK_SPACE) {
        if (expected) *expected = (BYTE)' ';
        return 1;
    }
    if (vk == UISET_VK_TAB) {
        if (expected) *expected = (BYTE)'\t';
        return 1;
    }
    if (vk == UISET_VK_BACK) {
        if (expected) *expected = (BYTE)'\b';
        return 1;
    }
    if (vk == UISET_VK_ESCAPE) {
        if (expected) *expected = (BYTE)0x1b;
        return 1;
    }
    if (vk == UISET_VK_RETURN) {
        if (expected) *expected = (BYTE)'\r';
        return 1;
    }
    return 0;
}

static BYTE ui_settings_key_scan(UISettingsLParam lParam) {
    return (BYTE)(((DWORD)lParam >> 16) & 0xffUL);
}

static BYTE ui_settings_key_extended(UISettingsLParam lParam) {
    return (BYTE)(((DWORD)lParam >> 24) & 1UL);
}

static void ui_settings_pending_char_retire_vk(DWORD vk) {
    unsigned int i = 0;
    while (i < g_ui_settings_pending_char_count) {
        if (g_ui_settings_pending_chars[i].vk == (BYTE)vk) {
            unsigned int j;
            for (j = i + 1; j < g_ui_settings_pending_char_count; ++j)
                g_ui_settings_pending_chars[j - 1] = g_ui_settings_pending_chars[j];
            --g_ui_settings_pending_char_count;
        } else {
            ++i;
        }
    }
}

static void ui_settings_pending_char_push(DWORD vk, DWORD mods,
                                           UISettingsLParam lParam) {
    BYTE expected;
    unsigned int i;
    if (vk > 255U || !ui_settings_key_is_printable(vk, mods, &expected)) return;
    if (g_ui_settings_pending_char_count >= UISET_PENDING_CHAR_CAP) {
        for (i = 1; i < UISET_PENDING_CHAR_CAP; ++i)
            g_ui_settings_pending_chars[i - 1] = g_ui_settings_pending_chars[i];
        g_ui_settings_pending_char_count = UISET_PENDING_CHAR_CAP - 1U;
    }
    g_ui_settings_pending_chars[g_ui_settings_pending_char_count].vk = (BYTE)vk;
    g_ui_settings_pending_chars[g_ui_settings_pending_char_count].scan =
        ui_settings_key_scan(lParam);
    g_ui_settings_pending_chars[g_ui_settings_pending_char_count].extended =
        ui_settings_key_extended(lParam);
    g_ui_settings_pending_chars[g_ui_settings_pending_char_count].expected = expected;
    ++g_ui_settings_pending_char_count;
}

static void ui_settings_key_state_clear(void) {
    unsigned int i;
    for (i = 0; i < 256U; ++i) g_ui_settings_consumed_keys[i] = 0;
    g_ui_settings_pending_char_count = 0;
}

static int ui_settings_key_was_consumed(DWORD vk) {
    return vk <= 255U && g_ui_settings_consumed_keys[vk] != 0;
}

static void ui_settings_mark_key_consumed(DWORD vk) {
    if (vk > 255U) return;
    g_ui_settings_consumed_keys[vk] = 1;
}

static void ui_settings_mark_key_char(DWORD vk, DWORD mods,
                                       UISettingsLParam lParam) {
    if (vk > 255U) return;
    ui_settings_pending_char_push(vk, mods, lParam);
}

static int ui_settings_char_matches(BYTE expected, DWORD value) {
    BYTE got = (BYTE)(value & 0xffUL);
    if (expected >= (BYTE)'A' && expected <= (BYTE)'Z')
        return got == expected || got == (BYTE)(expected + ((BYTE)'a' - (BYTE)'A'));
    return got == expected;
}

static int ui_settings_consume_pending_char(DWORD value, UISettingsLParam lParam) {
    unsigned int i;
    BYTE scan = ui_settings_key_scan(lParam);
    BYTE extended = ui_settings_key_extended(lParam);
    if (!g_ui_settings_pending_char_count) return 0;
    for (i = 0; i < g_ui_settings_pending_char_count; ++i) {
        UISettingsPendingChar* pending = &g_ui_settings_pending_chars[i];
        if (pending->scan && scan && pending->scan != scan) continue;
        if (pending->extended != extended && pending->scan && scan) continue;
        /* Once Windows gives us the originating scan code, it is stronger
           provenance than translated text (Shift+1 becomes '!'; Alt chords
           may arrive as WM_SYSCHAR).  Zero scan codes are fixture/IME
           fallbacks and retain the narrow character check. */
        if (!(pending->scan && scan) &&
            !ui_settings_char_matches(pending->expected, value)) continue;
        for (; i + 1 < g_ui_settings_pending_char_count; ++i)
            g_ui_settings_pending_chars[i] = g_ui_settings_pending_chars[i + 1];
        --g_ui_settings_pending_char_count;
        return 1;
    }
    return 0;
}

static int ui_settings_is_alt_f4(DWORD message, DWORD vk, UISettingsLParam lParam,
                                  DWORD mods) {
    if (vk != UISET_VK_F4) return 0;
    if (message != UISET_WM_SYSKEYDOWN) return 0;
    return (lParam & UISET_ALT_CONTEXT) != 0 || (mods & UIHK_ALT) != 0;
}

static UISettingsLResult WINAPI ui_settings_wndproc(HWND hwnd, DWORD message,
                                                     UISettingsWParam wParam,
                                                     UISettingsLParam lParam) {
    int open = __atomic_load_n(&g_ui_settings_panel_open, __ATOMIC_ACQUIRE) != 0;
    DWORD vk = (DWORD)wParam & 0xffUL;

    if (message == UISET_WM_KILLFOCUS ||
        (message == UISET_WM_ACTIVATEAPP && !wParam)) {
        ui_settings_key_state_clear();
        return ui_settings_forward(hwnd, message, wParam, lParam);
    }

    if (message == UISET_WM_KEYDOWN || message == UISET_WM_SYSKEYDOWN) {
        DWORD mods = ui_hotkeys_modifiers();
        DWORD mask;
        int repeat = (lParam & UISET_KEY_REPEAT) != 0;

        /* Alt+F4 remains the game's normal close command, even if a user
           assigns F4 to one of the configurable actions. */
        if (ui_settings_is_alt_f4(message, vk, lParam, mods))
            return ui_settings_forward(hwnd, message, wParam, lParam);

        mask = ui_hotkeys_match(vk, mods);
        if (ui_settings_key_was_consumed(vk)) {
            /* A held printable binding may produce several WM_CHAR messages;
               retain one scan-tagged record for each repeat. */
            if (repeat) ui_settings_mark_key_char(vk, mods, lParam);
            return 0;
        }
        if (!repeat && vk <= 255U) ui_settings_pending_char_retire_vk(vk);

        /* The overlay action is the only hotkey allowed to change panel state
           while it is open.  Repeated key-down messages stay consumed but do
           not enqueue a second toggle. */
        if (mask & ui_settings_hotkey_bit(UIHK_OVERLAY)) {
            ui_settings_mark_key_consumed(vk);
            ui_settings_mark_key_char(vk, mods, lParam);
            if (!repeat) ui_settings_event(UISET_EVENT_TOGGLE);
            return 0;
        }

        if (open) {
            /* These controls remain local to the settings panel and are
               independent of the configurable action bindings. */
            if (vk == UISET_VK_ESCAPE) ui_settings_event(UISET_EVENT_ESCAPE);
            else if (vk == UISET_VK_UP) ui_settings_event(UISET_EVENT_UP);
            else if (vk == UISET_VK_DOWN) ui_settings_event(UISET_EVENT_DOWN);
            else if (vk == UISET_VK_LEFT) ui_settings_event(UISET_EVENT_LEFT);
            else if (vk == UISET_VK_RIGHT) ui_settings_event(UISET_EVENT_RIGHT);
            else if (vk == UISET_VK_RETURN) ui_settings_event(UISET_EVENT_ENTER);
            else if (vk == UISET_VK_S) {
                ui_settings_mark_key_consumed(vk);
                ui_settings_mark_key_char(vk, mods, lParam);
                ui_settings_event(UISET_EVENT_SAVE);
            }
            /* Every other key-down is consumed while the panel is open. */
            return 0;
        }

        if (mask) {
            ui_settings_mark_key_consumed(vk);
            ui_settings_mark_key_char(vk, mods, lParam);
            if (!repeat) ui_hotkeys_queue(mask);
            return 0;
        }
    }

    if (message == UISET_WM_KEYUP || message == UISET_WM_SYSKEYUP) {
        /* Match provenance from key-down, rather than current modifier state;
           Shift/Ctrl/Alt often arrives as key-up before the bound key. */
        if (ui_settings_key_was_consumed(vk)) {
            g_ui_settings_consumed_keys[vk] = 0;
            return 0;
        }
    }

    if (message == UISET_WM_CHAR || message == UISET_WM_SYSCHAR) {
        /* TranslateMessage can enqueue WM_CHAR after the physical key-up.
           Consume only a bounded, character-specific record created by a
           matched key-down. */
        if (ui_settings_consume_pending_char((DWORD)wParam, lParam)) return 0;
        if (open) return 0;
    }

    if (open && (message == UISET_WM_LBUTTONDOWN ||
                 message == UISET_WM_LBUTTONDBLCLK ||
                 message == UISET_WM_RBUTTONDOWN ||
                 message == UISET_WM_RBUTTONDBLCLK ||
                 message == UISET_WM_MBUTTONDOWN ||
                 message == UISET_WM_MBUTTONDBLCLK ||
                 message == UISET_WM_XBUTTONDOWN ||
                 message == UISET_WM_XBUTTONDBLCLK ||
                 message == UISET_WM_MOUSEWHEEL ||
                 message == UISET_WM_MOUSEHWHEEL)) return 0;
    if (message == UISET_WM_NCDESTROY) {
        UISettingsLResult result=ui_settings_forward(hwnd,message,wParam,lParam);
        ui_settings_key_state_clear();
        __atomic_store_n(&g_ui_settings_panel_open, 0, __ATOMIC_RELEASE);
        __atomic_store_n(&g_ui_settings_deferred_open, 0, __ATOMIC_RELEASE);
        __atomic_store_n(&g_ui_settings_subclass_state, 0, __ATOMIC_RELEASE);
        g_ui_settings_original_wndproc = 0;
        g_ui_settings_bound_hwnd = 0;
        return result;
    }
    return ui_settings_forward(hwnd, message, wParam, lParam);
}

static int ui_settings_install_subclass(void) {
    HWND hwnd;
    LONG previous;
    LONG expected = 0;
    if (__atomic_load_n(&g_ui_settings_subclass_state, __ATOMIC_ACQUIRE) == 2)
        return 1;
    if (__atomic_load_n(&g_ui_settings_subclass_state, __ATOMIC_ACQUIRE) == 3)
        return 0;
    if (!g_ui_settings_set_window_long || !g_ui_settings_call_window_proc) {
        __atomic_store_n(&g_ui_settings_subclass_state, 3, __ATOMIC_RELEASE);
        return 0;
    }
    if (!__atomic_compare_exchange_n(&g_ui_settings_subclass_state, &expected, 1,
                                     0, __ATOMIC_ACQ_REL, __ATOMIC_ACQUIRE))
        return 0;
    hwnd = ui_settings_game_hwnd();
    if (!hwnd) {
        /* The main HWND can be published after the first present. Retry on
           the next render poll instead of making an early frame terminal. */
        __atomic_store_n(&g_ui_settings_subclass_state, 0, __ATOMIC_RELEASE);
        return 0;
    }
    previous = g_ui_settings_set_window_long(
        hwnd, UISET_GWL_WNDPROC, (LONG)(ULONG_PTR)ui_settings_wndproc);
    if (!previous) {
        __atomic_store_n(&g_ui_settings_subclass_state, 3, __ATOMIC_RELEASE);
        return 0;
    }
    g_ui_settings_original_wndproc =
        (UISettingsWndProc)(ULONG_PTR)(DWORD)previous;
    g_ui_settings_bound_hwnd = hwnd;
    __atomic_store_n(&g_ui_settings_subclass_state, 2, __ATOMIC_RELEASE);
    return 1;
}

static void ui_settings_open_panel(void) {
    g_ui_settings_draft_percent = ui_settings_clamp_percent(g_ui_scale_percent);
    g_ui_settings_draft_enabled = g_ui_runtime_enabled != 0;
    g_ui_settings_draft_crisp = g_ui_sharp_filter != 0;
    g_ui_settings_draft_keep = g_ui_keep_on_screen != 0;
    g_ui_settings_selected = 0;
    g_ui_settings_status = 0;
    g_ui_settings_failure_logged = 0;
    __atomic_store_n(&g_ui_settings_deferred_open, 0, __ATOMIC_RELEASE);
    __atomic_store_n(&g_ui_settings_panel_open, 1, __ATOMIC_RELEASE);
}

static void ui_settings_close_panel(void) {
    __atomic_store_n(&g_ui_settings_panel_open, 0, __ATOMIC_RELEASE);
    __atomic_store_n(&g_ui_settings_deferred_open, 0, __ATOMIC_RELEASE);
    g_ui_settings_status = 0;
}

static void ui_settings_change_selected(int delta) {
    if (g_ui_settings_selected == 0) {
        g_ui_settings_draft_percent = ui_settings_clamp_percent(
            g_ui_settings_draft_percent + delta * 5);
    } else if (g_ui_settings_selected == 1) {
        g_ui_settings_draft_enabled = !g_ui_settings_draft_enabled;
    } else if (g_ui_settings_selected == 2) {
        g_ui_settings_draft_crisp = !g_ui_settings_draft_crisp;
    } else {
        g_ui_settings_draft_keep = !g_ui_settings_draft_keep;
    }
}

static void ui_settings_select_row(int delta) {
    int row = g_ui_settings_selected + delta;
    if (row < 0) row = 3;
    if (row > 3) row = 0;
    g_ui_settings_selected = row;
}

static void ui_settings_queue_draft(int save) {
    ui_settings_queue_values(g_ui_settings_draft_percent,
                             g_ui_settings_draft_enabled,
                             g_ui_settings_draft_crisp,
                             g_ui_settings_draft_keep, save);
    g_ui_settings_status = save ? 2 : 1;
}

static void ui_settings_drain_events(void) {
    DWORD events = __atomic_exchange_n(&g_ui_settings_events, 0, __ATOMIC_ACQ_REL);
    int open = __atomic_load_n(&g_ui_settings_panel_open, __ATOMIC_ACQUIRE) != 0;
    if (events & UISET_EVENT_TOGGLE) {
        if (open) ui_settings_close_panel();
        else if (owner_native_capture()) {
            LONG pending = __atomic_load_n(&g_ui_settings_deferred_open, __ATOMIC_ACQUIRE);
            __atomic_store_n(&g_ui_settings_deferred_open, pending ? 0 : 1,
                             __ATOMIC_RELEASE);
        }
        else ui_settings_open_panel();
        open = __atomic_load_n(&g_ui_settings_panel_open, __ATOMIC_ACQUIRE) != 0;
    }
    if (!open) {
        if (__atomic_load_n(&g_ui_settings_deferred_open, __ATOMIC_ACQUIRE) &&
            !owner_native_capture()) ui_settings_open_panel();
        return;
    }
    if (events & UISET_EVENT_ESCAPE) {
        ui_settings_close_panel();
        return;
    }
    if (events & UISET_EVENT_UP) ui_settings_select_row(-1);
    if (events & UISET_EVENT_DOWN) ui_settings_select_row(1);
    if (events & UISET_EVENT_LEFT) ui_settings_change_selected(-1);
    if (events & UISET_EVENT_RIGHT) ui_settings_change_selected(1);
    if (events & UISET_EVENT_ENTER) ui_settings_queue_draft(0);
    if (events & UISET_EVENT_SAVE) {
        ui_settings_queue_draft(1);
        ui_settings_close_panel();
    }
}

static void ui_settings_format_scale(char* out, unsigned int cap, int percent) {
    unsigned int i = 0;
    percent = ui_settings_clamp_percent(percent);
    if (!out || cap < 6) return;
    out[i++]='S'; out[i++]='c'; out[i++]='a'; out[i++]='l'; out[i++]='e'; out[i++]=':';
    if (i < cap) out[i++]=' ';
    if (percent >= 100 && i + 3 < cap) out[i++]=(char)('0' + percent / 100);
    if (i + 2 < cap) out[i++]=(char)('0' + (percent / 10) % 10);
    if (i + 1 < cap) out[i++]=(char)('0' + percent % 10);
    if (i + 1 < cap) out[i++]='%';
    if (i < cap) out[i]=0;
}

static int ui_settings_fill(void* dc, const RECT* rect, DWORD color) {
    void* brush;
    int result;
    if (!g_ui_settings_create_brush || !g_ui_settings_fill_rect ||
        !g_ui_settings_delete_object) return 0;
    brush = g_ui_settings_create_brush(color);
    if (!brush) return 0;
    result = g_ui_settings_fill_rect(dc, rect, brush);
    if (!g_ui_settings_delete_object(brush)) result = 0;
    return result != 0;
}

static int ui_settings_draw_line(void* dc, const RECT* area, const char* text) {
    RECT copy;
    int length = 0;
    if (!g_ui_settings_draw_text || !area || !text) return 0;
    while (text[length]) ++length;
    copy = *area;
    return g_ui_settings_draw_text(dc, text, length, &copy,
                                   UISET_DT_LEFT | UISET_DT_SINGLELINE |
                                   UISET_DT_VCENTER) != 0;
}

static int ui_settings_gdi_ready(void) {
    return g_ui_settings_save_dc && g_ui_settings_restore_dc &&
           g_ui_settings_create_brush && g_ui_settings_fill_rect &&
           g_ui_settings_delete_object && g_ui_settings_select_object &&
           g_ui_settings_set_bk_mode && g_ui_settings_set_text_color &&
           g_ui_settings_text_out && g_ui_settings_draw_text &&
           g_ui_settings_create_font;
}

/* Draw the panel directly into the current DirectDraw surface.  Surface
 * vtable slots are IDirectDrawSurface7::GetDC (17) and ReleaseDC (26). */
static void ui_settings_draw_surface(void* target) {
    void** vt;
    void* dc = 0;
    void* font = 0;
    void* old_font = 0;
    RECT panel, header, row, text;
    char scale_line[32];
    int vw, vh, pw, ph, font_px;
    int saved = 0, have_dc = 0, selected, ok = 0;
    HRESULT hr;
    PFN_UISettingsGetDC get_dc;
    PFN_UISettingsReleaseDC release_dc;
    if (!__atomic_load_n(&g_ui_settings_panel_open, __ATOMIC_ACQUIRE)) return;
    if (!target || !ui_settings_gdi_ready() || !mem_readable(target, 4)) {
        ui_settings_fail_close();
        return;
    }
    vt = *(void***)target;
    if (!vt || !mem_readable(vt + 17, sizeof(void*) * 10)) {
        ui_settings_fail_close();
        return;
    }
    get_dc = (PFN_UISettingsGetDC)vt[17];
    release_dc = (PFN_UISettingsReleaseDC)vt[26];
    if (!get_dc || !release_dc) {
        ui_settings_fail_close();
        return;
    }
    vw=(int)g_ui_screen_w; vh=(int)g_ui_screen_h;
    if (vw < UISET_PANEL_MIN_EDGE*2 || vh < UISET_PANEL_MIN_EDGE*2) {
        ui_settings_fail_close();
        return;
    }
    pw=UISET_PANEL_WIDTH; ph=UISET_PANEL_HEIGHT;
    if (pw > vw-UISET_PANEL_MIN_EDGE*2) pw=vw-UISET_PANEL_MIN_EDGE*2;
    if (ph > vh-UISET_PANEL_MIN_EDGE*2) ph=vh-UISET_PANEL_MIN_EDGE*2;
    if (pw < 240 || ph < UISET_PANEL_HEIGHT) {
        ui_settings_fail_close();
        return;
    }
    font_px=vh/60;
    if (font_px<UISET_FONT_MIN) font_px=UISET_FONT_MIN;
    if (font_px>UISET_FONT_MAX) font_px=UISET_FONT_MAX;
    panel.left=(vw-pw)/2; panel.top=(vh-ph)/2;
    panel.right=panel.left+pw; panel.bottom=panel.top+ph;
    hr=get_dc(target,&dc); have_dc=hr>=0;
    if (hr<0 || !dc) goto cleanup;
    saved=g_ui_settings_save_dc(dc);
    if (!saved) goto cleanup;
    if (!ui_settings_fill(dc,&panel,0x00201818UL)) goto cleanup;
    header=panel; header.bottom=header.top+44;
    if (!ui_settings_fill(dc,&header,0x00403020UL)) goto cleanup;
    font=g_ui_settings_create_font(-font_px,0,0,0,UISET_FW_NORMAL,0,0,0,
                                   UISET_DEFAULT_CHARSET,UISET_OUT_DEFAULT,
                                   UISET_CLIP_DEFAULT,UISET_DEFAULT_QUALITY,
                                   UISET_DEFAULT_PITCH|UISET_FF_DONTCARE,
                                   "Arial");
    if (!font) goto cleanup;
    old_font=g_ui_settings_select_object(dc,font);
    if (!old_font) goto cleanup;
    g_ui_settings_set_bk_mode(dc,UISET_TRANSPARENT);
    g_ui_settings_set_text_color(dc,0x00ffffffUL);
    text.left=panel.left+16; text.right=panel.right-16;
    text.top=panel.top+8; text.bottom=panel.top+38;
    if (!g_ui_settings_text_out(dc,text.left,text.top,"PRM UI FIX",10)) goto cleanup;
    ui_settings_format_scale(scale_line,sizeof(scale_line),g_ui_settings_draft_percent);
    row.left=panel.left+16; row.right=panel.right-16; row.top=panel.top+58; row.bottom=row.top+34;
    selected=g_ui_settings_selected==0; if (selected && !ui_settings_fill(dc,&row,0x00605030UL)) goto cleanup;
    text=row; text.left+=10; if (!ui_settings_draw_line(dc,&text,scale_line)) goto cleanup;
    row.top+=38; row.bottom+=38;
    selected=g_ui_settings_selected==1; if (selected && !ui_settings_fill(dc,&row,0x00605030UL)) goto cleanup;
    text=row; text.left+=10; if (!ui_settings_draw_line(dc,&text,g_ui_settings_draft_enabled?"Enable UI scaling":"Enable UI scaling [off]")) goto cleanup;
    row.top+=38; row.bottom+=38;
    selected=g_ui_settings_selected==2; if (selected && !ui_settings_fill(dc,&row,0x00605030UL)) goto cleanup;
    text=row; text.left+=10; if (!ui_settings_draw_line(dc,&text,g_ui_settings_draft_crisp?"Crisp filtering":"Crisp filtering [off]")) goto cleanup;
    row.top+=38; row.bottom+=38;
    selected=g_ui_settings_selected==3; if (selected && !ui_settings_fill(dc,&row,0x00605030UL)) goto cleanup;
    text=row; text.left+=10; if (!ui_settings_draw_line(dc,&text,g_ui_settings_draft_keep?"Keep on screen":"Keep on screen [off]")) goto cleanup;
    text.left=panel.left+16; text.right=panel.right-16;
    text.top=panel.bottom-72; text.bottom=panel.bottom-40;
    if (!ui_settings_draw_line(dc,&text,"Arrows: select / change    Enter: Apply")) goto cleanup;
    text.top=panel.bottom-36; text.bottom=panel.bottom-4;
    if (!ui_settings_draw_line(dc,&text,"S: Save and close    Esc: Close")) goto cleanup;
    ok=1;
cleanup:
    if (old_font && g_ui_settings_select_object) g_ui_settings_select_object(dc,old_font);
    if (font && g_ui_settings_delete_object) g_ui_settings_delete_object(font);
    if (saved && g_ui_settings_restore_dc && !g_ui_settings_restore_dc(dc,saved)) ok=0;
    if (have_dc && release_dc(target,dc)<0) ok=0;
    if (!ok) ui_settings_fail_close();
    (void)ok;
}

static int ui_settings_is_open(void) {
    return __atomic_load_n(&g_ui_settings_panel_open, __ATOMIC_ACQUIRE) != 0;
}

static void ui_settings_draw_failed(void) {
    if (__atomic_load_n(&g_ui_settings_panel_open, __ATOMIC_ACQUIRE))
        ui_settings_fail_close();
}

static void ui_settings_poll(void) {
    DWORD packet;
    ui_settings_publish_snapshot();
    ui_settings_resolve_apis();
    if (ui_settings_install_subclass()) ui_settings_drain_events();
    packet=__atomic_exchange_n(&g_ui_settings_mailbox,0,__ATOMIC_ACQ_REL);
    if (packet & UISET_PACKET_VALID)
        UI_SETTINGS_APPLY((int)(packet & UISET_PACKET_PERCENT),
                          (packet & UISET_PACKET_ENABLED)!=0,
                          (packet & UISET_PACKET_CRISP)!=0,
                          (packet & UISET_PACKET_KEEP)!=0,
                          (packet & UISET_PACKET_SAVE)!=0);
}

#endif /* PRM_UI_SETTINGS_H */
