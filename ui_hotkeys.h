#ifndef PRM_UI_HOTKEYS_H
#define PRM_UI_HOTKEYS_H

/*
 * Render-thread hotkey bindings.
 *
 * The header is intentionally freestanding.  It is included after the
 * proxy's path/bootstrap helpers, so module walking, export resolution,
 * g_ini_path, and log_line are already available.  Key state is sampled only
 * when a caller handles a real key event; this module never polls async key
 * state or consumes a Windows message.
 */

enum {
    UIHK_OVERLAY = 0,
    UIHK_FILTER,
    UIHK_SCALE,
    UIHK_INPUT,
    UIHK_GROUPS,
    UIHK_DIAGNOSTICS,
    UIHK_WORLD,
    UIHK_TRACE,
    UIHK_VIRTUAL_TRACE,
    UIHK_COUNT
};

#define UIHK_SHIFT 1UL
#define UIHK_CTRL  2UL
#define UIHK_ALT   4UL
#define UIHK_WIN   8UL
#define UIHK_MOD_MASK (UIHK_SHIFT | UIHK_CTRL | UIHK_ALT | UIHK_WIN)
#define UIHK_ALL_MASK ((1UL << UIHK_COUNT) - 1UL)

#define UIHK_VK_BACKSPACE 0x08UL
#define UIHK_VK_TAB       0x09UL
#define UIHK_VK_RETURN    0x0dUL
#define UIHK_VK_SHIFT     0x10UL
#define UIHK_VK_CONTROL   0x11UL
#define UIHK_VK_MENU      0x12UL
#define UIHK_VK_PGUP      0x21UL
#define UIHK_VK_PGDN      0x22UL
#define UIHK_VK_END       0x23UL
#define UIHK_VK_HOME      0x24UL
#define UIHK_VK_LEFT      0x25UL
#define UIHK_VK_UP        0x26UL
#define UIHK_VK_RIGHT     0x27UL
#define UIHK_VK_DOWN      0x28UL
#define UIHK_VK_INSERT    0x2dUL
#define UIHK_VK_DELETE    0x2eUL
#define UIHK_VK_SPACE     0x20UL
#define UIHK_VK_LWIN      0x5bUL
#define UIHK_VK_RWIN      0x5cUL

#define UIHK_PROFILE_SECTION "Keybinds"
#define UIHK_OVERLAY_DEFAULT "Shift+P"
#define UIHK_OVERLAY_MISSING "\x01prm-ui-hotkey-overlay-missing"
#define UIHK_TEXT_CAP 96U

typedef struct {
    DWORD vk;
    DWORD mods;
    int valid;
} UIHotkeyBinding;

typedef DWORD (WINAPI *PFN_UIHotkeysGetPrivateProfileStringA)(LPCSTR, LPCSTR,
                                                               LPCSTR, LPSTR,
                                                               DWORD, LPCSTR);
typedef short (WINAPI *PFN_UIHotkeysGetKeyState)(int);

static volatile LONG g_ui_hotkeys_api_state;
static volatile LONG g_ui_hotkeys_loaded;
static volatile DWORD g_ui_hotkey_queue;
static UIHotkeyBinding g_ui_hotkeys[UIHK_COUNT];
static PFN_UIHotkeysGetPrivateProfileStringA g_ui_hotkeys_get_profile;
static PFN_UIHotkeysGetKeyState g_ui_hotkeys_get_key_state;

static char ui_hotkeys_lower(char c) {
    return (c >= 'A' && c <= 'Z') ? (char)(c + ('a' - 'A')) : c;
}

static int ui_hotkeys_space(char c) {
    return c == ' ' || c == '\t' || c == '\r' || c == '\n' ||
           c == '\v' || c == '\f';
}

static unsigned int ui_hotkeys_len(const char* s) {
    unsigned int n = 0;
    if (!s) return 0;
    while (s[n]) ++n;
    return n;
}

static void ui_hotkeys_copy(char* dst, unsigned int cap, const char* src) {
    unsigned int i = 0;
    if (!dst || !cap) return;
    while (src && src[i] && i + 1 < cap) { dst[i] = src[i]; ++i; }
    dst[i] = 0;
}

static void ui_hotkeys_append(char* dst, unsigned int cap, const char* src) {
    unsigned int n = ui_hotkeys_len(dst), i = 0;
    if (!dst || !cap || n >= cap) return;
    while (src && src[i] && n + i + 1 < cap) { dst[n+i] = src[i]; ++i; }
    dst[n+i] = 0;
}

static int ui_hotkeys_blank(const char* text) {
    unsigned int i = 0;
    if (!text) return 1;
    while (text[i]) {
        if (!ui_hotkeys_space(text[i])) return 0;
        ++i;
    }
    return 1;
}

static int ui_hotkeys_equal(const char* a, const char* b) {
    unsigned int i = 0;
    if (!a || !b) return 0;
    while (a[i] && b[i]) {
        if (ui_hotkeys_lower(a[i]) != ui_hotkeys_lower(b[i])) return 0;
        ++i;
    }
    return a[i] == 0 && b[i] == 0;
}

static const char* ui_hotkeys_action_name(int action) {
    static const char* names[UIHK_COUNT] = {
        "Overlay", "ToggleFiltering", "ToggleScaling", "ToggleMouseRemap",
        "DumpGroups", "DumpDiagnostics", "ToggleWorldInput", "CaptureTrace",
        "CaptureVirtualTrace"
    };
    return (action >= 0 && action < UIHK_COUNT) ? names[action] : "Unknown";
}

static void ui_hotkeys_log_invalid(int action, int truncated) {
    char line[128];
    ui_hotkeys_copy(line, sizeof(line), truncated ?
                    "Hotkeys: truncated binding for " :
                    "Hotkeys: invalid binding for ");
    ui_hotkeys_append(line, sizeof(line), ui_hotkeys_action_name(action));
    log_line(line);
}

static void ui_hotkeys_clear(void) {
    int i;
    for (i = 0; i < UIHK_COUNT; ++i) {
        g_ui_hotkeys[i].vk = 0;
        g_ui_hotkeys[i].mods = 0;
        g_ui_hotkeys[i].valid = 0;
    }
}

static int ui_hotkeys_token(const char* text, unsigned int begin,
                            unsigned int end, char* out, unsigned int cap) {
    unsigned int i, n = 0;
    while (begin < end && ui_hotkeys_space(text[begin])) ++begin;
    while (end > begin && ui_hotkeys_space(text[end-1])) --end;
    if (begin == end || !out || !cap) return 0;
    for (i = begin; i < end; ++i) {
        if (ui_hotkeys_space(text[i])) continue;
        if (n + 1 >= cap) return 0;
        out[n++] = ui_hotkeys_lower(text[i]);
    }
    if (!n) return 0;
    out[n] = 0;
    return 1;
}

static int ui_hotkeys_modifier(const char* token, DWORD* bit) {
    if (ui_hotkeys_equal(token, "shift")) { *bit = UIHK_SHIFT; return 1; }
    if (ui_hotkeys_equal(token, "ctrl") ||
        ui_hotkeys_equal(token, "control")) { *bit = UIHK_CTRL; return 1; }
    if (ui_hotkeys_equal(token, "alt")) { *bit = UIHK_ALT; return 1; }
    if (ui_hotkeys_equal(token, "win") ||
        ui_hotkeys_equal(token, "windows") ||
        ui_hotkeys_equal(token, "super")) { *bit = UIHK_WIN; return 1; }
    return 0;
}

static int ui_hotkeys_key(const char* token, DWORD* vk) {
    unsigned int n, i, value;
    char c;
    if (!token || !vk) return 0;
    n = ui_hotkeys_len(token);
    if (n == 1) {
        c = token[0];
        if ((c >= 'a' && c <= 'z') || (c >= '0' && c <= '9')) {
            *vk = (DWORD)(unsigned char)c;
            if (c >= 'a' && c <= 'z') *vk -= (DWORD)('a' - 'A');
            return 1;
        }
    }
    if (n >= 2 && token[0] == 'f') {
        value = 0;
        for (i = 1; i < n; ++i) {
            unsigned int digit;
            if (token[i] < '0' || token[i] > '9') return 0;
            digit = (unsigned int)(token[i] - '0');
            if (value > (24U - digit) / 10U) return 0;
            value = value * 10U + digit;
        }
        if (value >= 1U && value <= 24U) { *vk = 0x6fU + value; return 1; }
        return 0;
    }
    if (ui_hotkeys_equal(token, "left"))      *vk = UIHK_VK_LEFT;
    else if (ui_hotkeys_equal(token, "right")) *vk = UIHK_VK_RIGHT;
    else if (ui_hotkeys_equal(token, "up"))    *vk = UIHK_VK_UP;
    else if (ui_hotkeys_equal(token, "down"))  *vk = UIHK_VK_DOWN;
    else if (ui_hotkeys_equal(token, "home"))  *vk = UIHK_VK_HOME;
    else if (ui_hotkeys_equal(token, "end"))   *vk = UIHK_VK_END;
    else if (ui_hotkeys_equal(token, "insert") || ui_hotkeys_equal(token, "ins"))
        *vk = UIHK_VK_INSERT;
    else if (ui_hotkeys_equal(token, "delete") || ui_hotkeys_equal(token, "del"))
        *vk = UIHK_VK_DELETE;
    else if (ui_hotkeys_equal(token, "pageup") || ui_hotkeys_equal(token, "pgup"))
        *vk = UIHK_VK_PGUP;
    else if (ui_hotkeys_equal(token, "pagedown") || ui_hotkeys_equal(token, "pgdn"))
        *vk = UIHK_VK_PGDN;
    else if (ui_hotkeys_equal(token, "space")) *vk = UIHK_VK_SPACE;
    else if (ui_hotkeys_equal(token, "tab"))   *vk = UIHK_VK_TAB;
    else if (ui_hotkeys_equal(token, "enter") || ui_hotkeys_equal(token, "return"))
        *vk = UIHK_VK_RETURN;
    else if (ui_hotkeys_equal(token, "esc") || ui_hotkeys_equal(token, "escape"))
        *vk = 0x1bU;
    else if (ui_hotkeys_equal(token, "backspace") || ui_hotkeys_equal(token, "back"))
        *vk = UIHK_VK_BACKSPACE;
    else return 0;
    return 1;
}

static int ui_hotkeys_parse(const char* text, DWORD* vk, DWORD* mods) {
    unsigned int i = 0, start, end;
    DWORD parsed_mods = 0, bit = 0, parsed_vk = 0;
    int have_key = 0;
    char token[40];
    if (!text || !vk || !mods) return 0;
    while (text[i]) {
        while (ui_hotkeys_space(text[i])) ++i;
        if (!text[i] || text[i] == '+') return 0;
        start = i;
        while (text[i] && text[i] != '+') ++i;
        end = i;
        if (!ui_hotkeys_token(text, start, end, token, sizeof(token))) return 0;
        if (ui_hotkeys_modifier(token, &bit)) {
            if (parsed_mods & bit) return 0;
            parsed_mods |= bit;
        } else {
            if (have_key || !ui_hotkeys_key(token, &parsed_vk)) return 0;
            have_key = 1;
        }
        while (ui_hotkeys_space(text[i])) ++i;
        if (!text[i]) break;
        if (text[i] != '+') return 0;
        ++i;
        if (!text[i]) return 0;
    }
    if (!have_key) return 0;
    *vk = parsed_vk;
    *mods = parsed_mods;
    return 1;
}

static void ui_hotkeys_resolve_apis(void) {
    HMODULE kernel32, user32;
    kernel32 = find_loaded_module("kernel32.dll");
    user32 = find_loaded_module("user32.dll");
    if (kernel32)
        g_ui_hotkeys_get_profile =
            (PFN_UIHotkeysGetPrivateProfileStringA)resolve_export(
                kernel32, "GetPrivateProfileStringA");
    if (user32)
        g_ui_hotkeys_get_key_state =
            (PFN_UIHotkeysGetKeyState)resolve_export(user32, "GetKeyState");
}

static void ui_hotkeys_load(void) {
    LONG expected = 0;
    int i;
    if (!__atomic_compare_exchange_n(&g_ui_hotkeys_api_state, &expected, 1, 0,
                                     __ATOMIC_ACQ_REL, __ATOMIC_ACQUIRE)) {
        while (__atomic_load_n(&g_ui_hotkeys_api_state, __ATOMIC_ACQUIRE) == 1) {}
        return;
    }
    ui_hotkeys_clear();
    ui_hotkeys_resolve_apis();
    if (!g_ui_hotkeys_get_profile) {
        log_line("Hotkeys: GetPrivateProfileStringA unavailable");
    } else {
        static const char* keys[UIHK_COUNT] = {
            "Overlay", "ToggleFiltering", "ToggleScaling", "ToggleMouseRemap",
            "DumpGroups", "DumpDiagnostics", "ToggleWorldInput", "CaptureTrace",
            "CaptureVirtualTrace"
        };
        for (i = 0; i < UIHK_COUNT; ++i) {
            char value[UIHK_TEXT_CAP];
            const char* fallback = i == UIHK_OVERLAY ? UIHK_OVERLAY_MISSING : "";
            DWORD copied, vk = 0, mods = 0;
            int missing_overlay;
            value[0] = 0;
            copied = g_ui_hotkeys_get_profile(UIHK_PROFILE_SECTION, keys[i],
                                               fallback, value, sizeof(value),
                                               g_ini_path);
            value[sizeof(value)-1] = 0;
            if (copied >= sizeof(value)-1) {
                ui_hotkeys_log_invalid(i, 1);
                continue;
            }
            missing_overlay = i == UIHK_OVERLAY &&
                              ui_hotkeys_equal(value, UIHK_OVERLAY_MISSING);
            if (missing_overlay) ui_hotkeys_copy(value, sizeof(value), UIHK_OVERLAY_DEFAULT);
            if (ui_hotkeys_blank(value)) continue; /* Blank disables the action. */
            if (!ui_hotkeys_parse(value, &vk, &mods)) {
                ui_hotkeys_log_invalid(i, 0);
                continue;
            }
            g_ui_hotkeys[i].vk = vk;
            g_ui_hotkeys[i].mods = mods;
            g_ui_hotkeys[i].valid = 1;
        }
    }
    __atomic_store_n(&g_ui_hotkeys_loaded, 1, __ATOMIC_RELEASE);
    __atomic_store_n(&g_ui_hotkeys_api_state, 2, __ATOMIC_RELEASE);
}

static DWORD ui_hotkeys_match(DWORD vk, DWORD mods) {
    DWORD result = 0;
    int i;
    if (__atomic_load_n(&g_ui_hotkeys_api_state, __ATOMIC_ACQUIRE) != 2)
        ui_hotkeys_load();
    for (i = 0; i < UIHK_COUNT; ++i)
        if (g_ui_hotkeys[i].valid && g_ui_hotkeys[i].vk == vk &&
            g_ui_hotkeys[i].mods == mods)
            result |= 1UL << i;
    return result;
}

static DWORD ui_hotkeys_modifiers(void) {
    DWORD result = 0;
    short state;
    if (!g_ui_hotkeys_get_key_state) return 0;
    state = g_ui_hotkeys_get_key_state((int)UIHK_VK_SHIFT);
    if (((unsigned short)state & 0x8000U) != 0) result |= UIHK_SHIFT;
    state = g_ui_hotkeys_get_key_state((int)UIHK_VK_CONTROL);
    if (((unsigned short)state & 0x8000U) != 0) result |= UIHK_CTRL;
    state = g_ui_hotkeys_get_key_state((int)UIHK_VK_MENU);
    if (((unsigned short)state & 0x8000U) != 0) result |= UIHK_ALT;
    state = g_ui_hotkeys_get_key_state((int)UIHK_VK_LWIN);
    if (((unsigned short)state & 0x8000U) != 0) result |= UIHK_WIN;
    state = g_ui_hotkeys_get_key_state((int)UIHK_VK_RWIN);
    if (((unsigned short)state & 0x8000U) != 0) result |= UIHK_WIN;
    return result;
}

static void ui_hotkeys_queue(DWORD mask) {
    __atomic_fetch_or(&g_ui_hotkey_queue, mask & UIHK_ALL_MASK, __ATOMIC_RELEASE);
}

static int ui_hotkey_take(int action) {
    DWORD bit;
    if (action < 0 || action >= UIHK_COUNT) return 0;
    bit = 1UL << action;
    return (__atomic_fetch_and(&g_ui_hotkey_queue, ~bit, __ATOMIC_ACQ_REL) & bit) != 0;
}

#endif /* PRM_UI_HOTKEYS_H */
