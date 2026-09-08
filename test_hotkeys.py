#!/usr/bin/env python3
"""Exercise the freestanding render-thread hotkey parser and mailbox."""

from pathlib import Path
import os
import re
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parent
HEADER = (ROOT / "ui_hotkeys.h").read_text()
SOURCE = (ROOT / "prm_uifix.c").read_text()
CONSUMERS = "\n".join(re.search(
    r"static void " + name + r"\(void\) \{.*?^\}", SOURCE, re.M | re.S
).group(0) for name in (
    "maybe_toggle_ui_sharp", "maybe_toggle_ui_scale",
    "maybe_toggle_ui_input", "maybe_toggle_world_input"))

# The owner-trace action was deliberately removed because production has no
# consumer for it.  Keep this test from silently accepting a no-op binding.
assert "UIHK_OWNER_TRACE" not in HEADER
assert "CaptureOwnerTrace" not in HEADER


FIXTURE = r'''
#include <assert.h>
#include <stdint.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <pthread.h>

typedef uint8_t BYTE;
typedef uint16_t WORD;
typedef uint32_t UINT;
typedef int32_t LONG;
typedef uint32_t DWORD;
typedef uintptr_t ULONG_PTR;
typedef void *HMODULE;
typedef const char *LPCSTR;
typedef char *LPSTR;
#define WINAPI __attribute__((stdcall))

static char g_ini_path[64] = "fixture.ini";
static int g_kernel32_available = 1;
static int g_user32_available = 1;
static int g_profile_calls;
static int g_key_calls;
static int g_log_count;
static char g_last_log[160];
static char g_profile_text[9][256];
static int g_profile_present[9];
static unsigned char g_key_down[256];

static const char *const g_profile_keys[9] = {
    "Overlay", "ToggleFiltering", "ToggleScaling", "ToggleMouseRemap",
    "DumpGroups", "DumpDiagnostics", "ToggleWorldInput", "CaptureTrace",
    "CaptureVirtualTrace"
};

static int profile_index(const char *key) {
    int i;
    for (i = 0; i < 9; ++i)
        if (!strcmp(key, g_profile_keys[i])) return i;
    return -1;
}

static void log_line(const char *line) {
    size_t n = line ? strlen(line) : 0;
    if (n >= sizeof(g_last_log)) n = sizeof(g_last_log) - 1;
    if (line && n) memcpy(g_last_log, line, n);
    g_last_log[n] = 0;
    ++g_log_count;
}

static DWORD WINAPI fake_get_profile(LPCSTR section, LPCSTR key, LPCSTR def,
                                     LPSTR out, DWORD size, LPCSTR path) {
    const char *value = def ? def : "";
    size_t length, copied;
    int index;
    assert(!strcmp(section, "Keybinds"));
    assert(!strcmp(path, g_ini_path));
    ++g_profile_calls;
    index = profile_index(key);
    if (index >= 0 && g_profile_present[index]) value = g_profile_text[index];
    length = strlen(value);
    copied = size ? (length < (size_t)size - 1 ? length : (size_t)size - 1) : 0;
    if (size) {
        if (copied) memcpy(out, value, copied);
        out[copied] = 0;
    }
    return (DWORD)(length >= size && size ? size - 1 : length);
}

static short WINAPI fake_get_key_state(int vk) {
    ++g_key_calls;
    assert(vk >= 0 && vk < (int)sizeof(g_key_down));
    return g_key_down[vk] ? (short)-32768 : (short)0;
}

static HMODULE g_kernel32_module = (HMODULE)(ULONG_PTR)0x1001UL;
static HMODULE g_user32_module = (HMODULE)(ULONG_PTR)0x1002UL;

static HMODULE find_loaded_module(const char *name) {
    if (!strcmp(name, "kernel32.dll"))
        return g_kernel32_available ? g_kernel32_module : (HMODULE)0;
    if (!strcmp(name, "user32.dll"))
        return g_user32_available ? g_user32_module : (HMODULE)0;
    return (HMODULE)0;
}

static void *resolve_export(HMODULE module, const char *name) {
    if (module == g_kernel32_module &&
        !strcmp(name, "GetPrivateProfileStringA"))
        return (void *)(uintptr_t)fake_get_profile;
    if (module == g_user32_module && !strcmp(name, "GetKeyState"))
        return (void *)(uintptr_t)fake_get_key_state;
    return (void *)0;
}

#include "ui_hotkeys.h"

static void reset_fixture(void) {
    memset(g_profile_text, 0, sizeof(g_profile_text));
    memset(g_profile_present, 0, sizeof(g_profile_present));
    memset(g_key_down, 0, sizeof(g_key_down));
    memset(g_last_log, 0, sizeof(g_last_log));
    g_kernel32_available = 1;
    g_user32_available = 1;
    g_profile_calls = 0;
    g_key_calls = 0;
    g_log_count = 0;
    g_ui_hotkeys_api_state = 0;
    g_ui_hotkeys_loaded = 0;
    g_ui_hotkey_queue = 0;
    g_ui_hotkeys_get_profile = (PFN_UIHotkeysGetPrivateProfileStringA)0;
    g_ui_hotkeys_get_key_state = (PFN_UIHotkeysGetKeyState)0;
    ui_hotkeys_clear();
}

static void profile_set(int action, const char *value) {
    size_t n;
    assert(action >= 0 && action < 9);
    assert(value);
    n = strlen(value);
    assert(n < sizeof(g_profile_text[action]));
    memcpy(g_profile_text[action], value, n + 1);
    g_profile_present[action] = 1;
}

static void expect_match(DWORD vk, DWORD mods, DWORD expected) {
    assert(ui_hotkeys_match(vk, mods) == expected);
}

static void test_defaults_and_blank(void) {
    reset_fixture();
    ui_hotkeys_load();
    assert(UIHK_COUNT == 9);
    assert(g_ui_hotkeys_loaded == 1);
    assert(g_profile_calls == UIHK_COUNT);
    expect_match((DWORD)'P', UIHK_SHIFT, 1UL << UIHK_OVERLAY);
    expect_match((DWORD)'P', 0, 0);
    expect_match((DWORD)'A', 0, 0);
    /* Loading is one-shot and a match does not reread the profile. */
    assert(g_profile_calls == UIHK_COUNT);

    reset_fixture();
    profile_set(UIHK_OVERLAY, "");
    profile_set(UIHK_FILTER, "  Control + A  ");
    profile_set(UIHK_SCALE, " \t ");
    ui_hotkeys_load();
    expect_match((DWORD)'P', UIHK_SHIFT, 0);
    expect_match((DWORD)'A', UIHK_CTRL, 1UL << UIHK_FILTER);
    expect_match((DWORD)'A', 0, 0);
    assert(g_log_count == 0); /* Empty and whitespace-only values disable. */

    reset_fixture();
    /* ui_hotkeys_match is safe for the first event before explicit init. */
    expect_match((DWORD)'P', UIHK_SHIFT, 1UL << UIHK_OVERLAY);
    assert(g_profile_calls == UIHK_COUNT);
}

static void test_parser_and_duplicates(void) {
    DWORD vk, mods;

    assert(ui_hotkeys_parse(" shift + Page Up ", &vk, &mods));
    assert(vk == UIHK_VK_PGUP && mods == UIHK_SHIFT);
    assert(ui_hotkeys_parse("WIN + F24", &vk, &mods));
    assert(vk == 0x87UL && mods == UIHK_WIN);
    assert(ui_hotkeys_parse("Alt + PgDn", &vk, &mods));
    assert(vk == UIHK_VK_PGDN && mods == UIHK_ALT);
    assert(ui_hotkeys_parse("Control+Delete", &vk, &mods));
    assert(vk == UIHK_VK_DELETE && mods == UIHK_CTRL);
    assert(ui_hotkeys_parse("Esc", &vk, &mods));
    assert(vk == 0x1bUL && mods == 0);
    assert(!ui_hotkeys_parse("Shift+P+", &vk, &mods));
    assert(!ui_hotkeys_parse("Shift+Shift+P", &vk, &mods));
    assert(!ui_hotkeys_parse("A+B", &vk, &mods));
    assert(!ui_hotkeys_parse("+P", &vk, &mods));
    assert(!ui_hotkeys_parse("Ctrl+", &vk, &mods));
    assert(!ui_hotkeys_parse("F4294967297", &vk, &mods));

    reset_fixture();
    profile_set(UIHK_OVERLAY, "ctrl + p");
    profile_set(UIHK_FILTER, "CONTROL+P");
    profile_set(UIHK_SCALE, "alt+f12");
    profile_set(UIHK_INPUT, "win+f1");
    profile_set(UIHK_GROUPS, "left");
    profile_set(UIHK_DIAGNOSTICS, "Page Down");
    profile_set(UIHK_WORLD, "space");
    profile_set(UIHK_TRACE, "return");
    profile_set(UIHK_VIRTUAL_TRACE, "back");
    ui_hotkeys_load();
    expect_match((DWORD)'P', UIHK_CTRL,
                 (1UL << UIHK_OVERLAY) | (1UL << UIHK_FILTER));
    expect_match((DWORD)'P', UIHK_CTRL | UIHK_SHIFT, 0);
    expect_match(0x7bUL, UIHK_ALT, 1UL << UIHK_SCALE); /* F12. */
    expect_match(0x70UL, UIHK_WIN, 1UL << UIHK_INPUT); /* F1. */
    expect_match(UIHK_VK_LEFT, 0, 1UL << UIHK_GROUPS);
    expect_match(UIHK_VK_PGDN, 0, 1UL << UIHK_DIAGNOSTICS);
    expect_match(UIHK_VK_SPACE, 0, 1UL << UIHK_WORLD);
    expect_match(UIHK_VK_RETURN, 0, 1UL << UIHK_TRACE);
    expect_match(UIHK_VK_BACKSPACE, 0, 1UL << UIHK_VIRTUAL_TRACE);
}

static void test_invalid_and_truncated(void) {
    char long_value[96];
    int i;
    for (i = 0; i < (int)sizeof(long_value) - 1; ++i) long_value[i] = 'A';
    long_value[sizeof(long_value) - 1] = 0;

    reset_fixture();
    profile_set(UIHK_OVERLAY, "Ctrl+Bogus");
    profile_set(UIHK_FILTER, "Shift+P+Q");
    profile_set(UIHK_SCALE, "F25");
    profile_set(UIHK_INPUT, "Ctrl+");
    profile_set(UIHK_GROUPS, "++");
    profile_set(UIHK_DIAGNOSTICS, "Shift+Shift+P");
    profile_set(UIHK_WORLD, "A+B");
    profile_set(UIHK_TRACE, "NotAKey");
    profile_set(UIHK_VIRTUAL_TRACE, long_value);
    ui_hotkeys_load();
    assert(g_log_count == UIHK_COUNT);
    assert(strstr(g_last_log, "truncated") != 0);
    /* An explicit invalid Overlay value never falls back to Shift+P. */
    expect_match((DWORD)'P', UIHK_SHIFT, 0);
    expect_match((DWORD)'A', 0, 0);
    expect_match(0x87UL, 0, 0);

    reset_fixture();
    g_kernel32_available = 0;
    g_user32_available = 0;
    ui_hotkeys_load();
    assert(g_profile_calls == 0);
    assert(g_log_count == 1);
    expect_match((DWORD)'P', UIHK_SHIFT, 0);
    assert(ui_hotkeys_modifiers() == 0);
}

static void test_modifiers(void) {
    reset_fixture();
    ui_hotkeys_load();
    g_key_down[UIHK_VK_SHIFT] = 1;
    g_key_down[UIHK_VK_CONTROL] = 1;
    g_key_down[UIHK_VK_MENU] = 1;
    g_key_down[UIHK_VK_LWIN] = 1;
    assert(ui_hotkeys_modifiers() ==
           (UIHK_SHIFT | UIHK_CTRL | UIHK_ALT | UIHK_WIN));
    assert(g_key_calls == 5); /* Both Win keys are sampled for one bit. */

    g_key_calls = 0;
    g_key_down[UIHK_VK_SHIFT] = 0;
    g_key_down[UIHK_VK_CONTROL] = 0;
    g_key_down[UIHK_VK_MENU] = 0;
    g_key_down[UIHK_VK_LWIN] = 0;
    g_key_down[UIHK_VK_RWIN] = 1;
    g_key_down[0x14] = 1; /* An unrelated key cannot add a modifier. */
    assert(ui_hotkeys_modifiers() == UIHK_WIN);
    assert(g_key_calls == 5);
}

static void test_queue(void) {
    DWORD known = (1UL << UIHK_OVERLAY) | (1UL << UIHK_FILTER) |
                  (1UL << UIHK_VIRTUAL_TRACE);
    reset_fixture();
    ui_hotkeys_queue(known | (1UL << UIHK_COUNT));
    ui_hotkeys_queue(1UL << UIHK_FILTER); /* OR is idempotent. */
    assert(ui_hotkey_take(UIHK_OVERLAY));
    assert(!ui_hotkey_take(UIHK_OVERLAY));
    assert(ui_hotkey_take(UIHK_FILTER));
    assert(ui_hotkey_take(UIHK_VIRTUAL_TRACE));
    assert(!ui_hotkey_take(UIHK_VIRTUAL_TRACE));
    assert(!ui_hotkey_take(-1));
    assert(!ui_hotkey_take(UIHK_COUNT));
    assert(__atomic_load_n(&g_ui_hotkey_queue, __ATOMIC_ACQUIRE) == 0);

    ui_hotkeys_queue(0xffffffffUL);
    assert(__atomic_load_n(&g_ui_hotkey_queue, __ATOMIC_ACQUIRE) == UIHK_ALL_MASK);
    for (int i = 0; i < UIHK_COUNT; ++i) {
        assert(ui_hotkey_take(i));
        assert(!ui_hotkey_take(i));
    }
    assert(__atomic_load_n(&g_ui_hotkey_queue, __ATOMIC_ACQUIRE) == 0);
}

static void *queue_worker(void *unused) {
    int i;
    (void)unused;
    for (i = 0; i < 20000; ++i)
        ui_hotkeys_queue(UIHK_ALL_MASK);
    return 0;
}

static void *take_worker(void *unused) {
    int i;
    (void)unused;
    for (i = 0; i < 20000; ++i)
        (void)ui_hotkey_take(i % UIHK_COUNT);
    return 0;
}

static void test_queue_concurrency(void) {
    pthread_t producers[2], consumers[2];
    int i;
    reset_fixture();
    for (i = 0; i < 2; ++i)
        assert(!pthread_create(&producers[i], 0, queue_worker, 0));
    for (i = 0; i < 2; ++i)
        assert(!pthread_join(producers[i], 0));
    assert(__atomic_load_n(&g_ui_hotkey_queue, __ATOMIC_ACQUIRE) == UIHK_ALL_MASK);
    for (i = 0; i < 2; ++i)
        assert(!pthread_create(&consumers[i], 0, take_worker, 0));
    for (i = 0; i < 2; ++i)
        assert(!pthread_join(consumers[i], 0));
    assert(__atomic_load_n(&g_ui_hotkey_queue, __ATOMIC_ACQUIRE) == 0);
}

/* Actual production consumers share the message-thread mailbox. */
static int g_ui_sharp_filter, g_ui_runtime_enabled;
static int g_input_runtime_enabled, g_world_input_enabled;
__PRODUCTION_CONSUMERS__

static void test_production_consumers(void) {
    reset_fixture();
    g_ui_sharp_filter = g_ui_runtime_enabled = 0;
    g_input_runtime_enabled = g_world_input_enabled = 0;
    ui_hotkeys_queue((1UL << UIHK_SCALE) | (1UL << UIHK_WORLD));
    maybe_toggle_ui_sharp();
    maybe_toggle_ui_input();
    assert(!g_ui_sharp_filter && !g_input_runtime_enabled);
    maybe_toggle_ui_scale();
    assert(g_ui_runtime_enabled && !g_world_input_enabled);
    maybe_toggle_world_input();
    assert(g_world_input_enabled);
    maybe_toggle_ui_scale();
    maybe_toggle_world_input();
    assert(g_ui_runtime_enabled && g_world_input_enabled);
    ui_hotkeys_queue((1UL << UIHK_FILTER) | (1UL << UIHK_INPUT));
    maybe_toggle_ui_sharp();
    maybe_toggle_ui_input();
    assert(g_ui_sharp_filter && g_input_runtime_enabled);
    assert(!g_ui_hotkey_queue);
}

int main(void) {
    test_defaults_and_blank();
    test_parser_and_duplicates();
    test_invalid_and_truncated();
    test_modifiers();
    test_queue();
    test_queue_concurrency();
    test_production_consumers();
    puts("hotkey fixture: ok");
    return 0;
}
'''


def main():
    compiler = os.environ.get("CC", "clang")
    with tempfile.TemporaryDirectory(prefix="prm-hotkeys-") as directory:
        directory = Path(directory)
        fixture = directory / "hotkeys.c"
        binary = directory / "hotkeys"
        fixture.write_text(FIXTURE.replace("__PRODUCTION_CONSUMERS__", CONSUMERS))
        subprocess.run([
            compiler, "-m32", "-std=c11", "-O1", "-g", "-Wall", "-Wextra",
            "-Werror", "-pthread", "-I", str(ROOT), str(fixture), "-o",
            str(binary)
        ], check=True)
        subprocess.run([str(binary)], check=True)


if __name__ == "__main__":
    main()
