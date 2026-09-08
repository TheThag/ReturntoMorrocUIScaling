#!/usr/bin/env python3
"""Exercise the production OptionInfo.lua path/read/load helpers.

The harness extracts the three file-I/O helpers from prm_uifix.c and supplies
stdcall Win32 stubs.  It deliberately leaves parsing in ui_resolution.h, so
these tests cover the integration boundary: path construction, bounded reads,
handle cleanup, and atomic fallback/override behavior.
"""

from pathlib import Path
import os
import re
import shlex
import subprocess
import sys
import tempfile

from test_resolution import expected_generated_resolution


ROOT = Path(__file__).resolve().parent
SOURCE = (ROOT / "prm_uifix.c").read_text()
RESOLUTION_HEADER = (ROOT / "ui_resolution.h").read_text()


def extract_function(name: str) -> str:
    start = re.search(
        r"^static\s+[A-Za-z_][A-Za-z0-9_\s\*]*\b" + re.escape(name) +
        r"\s*\([^;]*?\)\s*\{", SOURCE, re.M
    )
    if not start:
        raise RuntimeError(f"missing production helper {name}")
    opening = SOURCE.find("{", start.start())
    tokens = re.finditer(
        r"/\*.*?\*/|//[^\n]*|\"(?:\\.|[^\"\\])*\"|"
        r"'(?:\\.|[^'\\])*'|[{}]", SOURCE[opening:], re.S
    )
    depth = 0
    for token in tokens:
        if token[0] == "{":
            depth += 1
        elif token[0] == "}":
            depth -= 1
            if depth == 0:
                return SOURCE[start.start():opening + token.end()]
    raise RuntimeError(f"unterminated production helper {name}")


FUNCTIONS = "\n\n".join(extract_function(name) for name in (
    "ui_resolution_path", "ui_resolution_read", "ui_resolution_load"
))


PREFIX = r'''
#include <assert.h>
#include <stdint.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef uint8_t BYTE;
typedef uint32_t DWORD;
typedef int32_t LONG;
typedef uintptr_t ULONG_PTR;
typedef void *HANDLE;
typedef void *HMODULE;
typedef void *LPVOID;
typedef const void *LPCVOID;
typedef const char *LPCSTR;
typedef char *LPSTR;
typedef int BOOL;
#define WINAPI __attribute__((stdcall))
#define GENERIC_READ 0x80000000UL
#define FILE_SHARE_READ 0x00000001UL
#define FILE_SHARE_WRITE 0x00000002UL
#define OPEN_EXISTING 3UL
#define FILE_ATTRIBUTE_NORMAL 0x00000080UL
#define INVALID_HANDLE_VALUE ((HANDLE)(ULONG_PTR)-1)

typedef HANDLE (WINAPI *PFN_CreateFileA)(LPCSTR,DWORD,DWORD,LPVOID,DWORD,DWORD,HANDLE);
typedef BOOL (WINAPI *PFN_ReadFile)(HANDLE,LPVOID,DWORD,DWORD*,LPVOID);
typedef BOOL (WINAPI *PFN_CloseHandle)(HANDLE);

static PFN_CreateFileA g_CreateFileA;
static PFN_ReadFile g_ReadFile;
static PFN_CloseHandle g_CloseHandle;
static char g_dll_path[520];
static int g_ui_auto_resolution=1;
static LONG g_ui_screen_w=3440;
static LONG g_ui_screen_h=1440;
static int g_log_count;
static char g_last_log[256];

static unsigned char g_file_token;
static const unsigned char *g_file_data;
static DWORD g_file_size;
static DWORD g_file_pos;
static DWORD g_read_chunk;
static int g_open_fail;
static int g_read_fail;
static int g_bad_got;
static int g_close_result=1;
static int g_open_calls;
static int g_read_calls;
static int g_close_calls;
static int g_path_calls;

static void log_line(const char *s) {
    ++g_log_count;
    if (!s) { g_last_log[0]=0; return; }
    strncpy(g_last_log,s,sizeof(g_last_log)-1);
    g_last_log[sizeof(g_last_log)-1]=0;
}

static HANDLE WINAPI fake_CreateFileA(LPCSTR path,DWORD access,DWORD share,LPVOID sec,
                                      DWORD disposition,DWORD attrs,HANDLE template_file) {
    (void)access; (void)share; (void)sec; (void)disposition; (void)attrs;
    (void)template_file;
    ++g_open_calls;
    if (path) ++g_path_calls;
    if (g_open_fail) return INVALID_HANDLE_VALUE;
    g_file_pos=0;
    return (HANDLE)&g_file_token;
}

static BOOL WINAPI fake_ReadFile(HANDLE file,LPVOID out,DWORD want,DWORD *got,LPVOID overlapped) {
    DWORD available, take;
    (void)overlapped;
    assert(file==(HANDLE)&g_file_token);
    ++g_read_calls;
    if (got) *got=0;
    if (g_read_fail) return 0;
    if (g_bad_got) {
        if (got) *got=want+1;
        return 1;
    }
    if (g_file_pos>=g_file_size) return 1;
    available=g_file_size-g_file_pos;
    take=available<want?available:want;
    if (g_read_chunk && take>g_read_chunk) take=g_read_chunk;
    if (take && out) memcpy(out,g_file_data+g_file_pos,take);
    g_file_pos+=take;
    if (got) *got=take;
    return 1;
}

static BOOL WINAPI fake_CloseHandle(HANDLE file) {
    assert(file==(HANDLE)&g_file_token);
    ++g_close_calls;
    return g_close_result?1:0;
}

static void reset_io(const unsigned char *data,DWORD size) {
    g_file_data=data; g_file_size=size; g_file_pos=0;
    g_read_chunk=0; g_open_fail=0; g_read_fail=0; g_bad_got=0;
    g_close_result=1; g_open_calls=0; g_read_calls=0; g_close_calls=0;
    g_path_calls=0; g_log_count=0; g_last_log[0]=0;
    g_CreateFileA=fake_CreateFileA;
    g_ReadFile=fake_ReadFile;
    g_CloseHandle=fake_CloseHandle;
}

static void set_path(const char *path) {
    memset(g_dll_path,0,sizeof(g_dll_path));
    if (path) {
        size_t n=strlen(path);
        assert(n<sizeof(g_dll_path));
        memcpy(g_dll_path,path,n+1);
    }
}

static void assert_dims(LONG width,LONG height) {
    assert(g_ui_screen_w==width);
    assert(g_ui_screen_h==height);
}

static const char basic_file[] =
    "OptionInfoList[\"WIDTH\"] = 1920\n"
    "OptionInfoList[\"HEIGHT\"] = 1080\n";
static const char invalid_file[] =
    "OptionInfoList[\"WIDTH\"] = 1920\n";
static unsigned char exact_file[65536];
static unsigned char over_file[65537];

static void make_boundary_files(void) {
    static const char prefix[] =
        "OptionInfoList[\"WIDTH\"] = 2560\n"
        "OptionInfoList[\"HEIGHT\"] = 1440\n";
    memset(exact_file,'\n',sizeof(exact_file));
    memset(over_file,'\n',sizeof(over_file));
    memcpy(exact_file,prefix,sizeof(prefix)-1);
    memcpy(over_file,prefix,sizeof(prefix)-1);
}

'''


def c_hex(data: bytes) -> str:
    if not data:
        return "0"
    return ",".join(f"0x{byte:02x}" for byte in data)



# Keep the fixture text separate so the generated C order is easy to inspect.
TESTS = r'''
static void test_paths(void) {
    char out[128];
    const char expected[]="C:/Games/Refuge/savedata\\OptionInfo.lua";
    DWORD need=(DWORD)strlen(expected)+1;
    set_path("C:/Games/Refuge/prm-uifix.dll");
    memset(out,'?',sizeof(out));
    assert(ui_resolution_path(out,sizeof(out)));
    assert(!strcmp(out,expected));
    memset(out,'?',sizeof(out));
    assert(ui_resolution_path(out,need));
    assert(!strcmp(out,expected));
    out[0]='?';
    assert(!ui_resolution_path(out,need-1));
    assert(out[0]=='?');
    assert(!ui_resolution_path(out,0));
    set_path("prm-uifix.dll");
    out[0]='?';
    assert(!ui_resolution_path(out,sizeof(out)) && out[0]=='?');
    memset(g_dll_path,'R',sizeof(g_dll_path));
    g_dll_path[5]='\\'; /* retain a directory while omitting the terminator */
    assert(!ui_resolution_path(out,sizeof(out)));
    puts("PASS resolution path: module-directory suffix, exact capacity, and bounded/truncated inputs");
}

static void test_read_failures(void) {
    LONG width=11,height=22;
    reset_io((const unsigned char*)basic_file,(DWORD)strlen(basic_file));
    assert(ui_resolution_read("savedata\\OptionInfo.lua",&width,&height));
    assert(width==1920 && height==1080);
    assert(g_open_calls==1 && g_close_calls==1 && g_read_calls>=2);
    reset_io((const unsigned char*)basic_file,(DWORD)strlen(basic_file));
    g_read_chunk=2;
    assert(ui_resolution_read("relative",&width,&height));
    assert(g_close_calls==1 && g_read_calls>2);
    reset_io((const unsigned char*)invalid_file,(DWORD)strlen(invalid_file));
    width=31; height=42;
    assert(!ui_resolution_read("invalid-pair",&width,&height));
    assert(width==31 && height==42);
    reset_io((const unsigned char*)basic_file,(DWORD)strlen(basic_file));
    g_close_result=0;
    assert(ui_resolution_read("close-fails",&width,&height));
    assert(g_close_calls==1);
    reset_io((const unsigned char*)basic_file,(DWORD)strlen(basic_file));
    g_open_fail=1;
    assert(!ui_resolution_read("open-fails",&width,&height));
    assert(g_open_calls==1 && g_close_calls==0);
    reset_io((const unsigned char*)basic_file,(DWORD)strlen(basic_file));
    g_read_fail=1;
    assert(!ui_resolution_read("read-fails",&width,&height));
    assert(g_open_calls==1 && g_close_calls==1);
    reset_io((const unsigned char*)basic_file,(DWORD)strlen(basic_file));
    g_bad_got=1;
    assert(!ui_resolution_read("bad-count",&width,&height));
    assert(g_close_calls==1);
    reset_io((const unsigned char*)basic_file,(DWORD)strlen(basic_file));
    g_CreateFileA=0;
    assert(!ui_resolution_read("missing-open",&width,&height));
    assert(g_open_calls==0 && g_close_calls==0);
    reset_io((const unsigned char*)basic_file,(DWORD)strlen(basic_file));
    g_ReadFile=0;
    assert(!ui_resolution_read("missing-read",&width,&height));
    assert(g_open_calls==0 && g_close_calls==0);
    reset_io((const unsigned char*)basic_file,(DWORD)strlen(basic_file));
    g_CloseHandle=0;
    assert(!ui_resolution_read("missing-close",&width,&height));
    assert(g_open_calls==0 && g_close_calls==0);
    puts("PASS resolution I/O failures: missing APIs, open/read errors, malformed counts, short reads, and handle closure");
}

static void test_limits(void) {
    LONG width=77,height=88;
    make_boundary_files();
    reset_io(exact_file,sizeof(exact_file));
    assert(ui_resolution_read("exact-64k",&width,&height));
    assert(width==2560 && height==1440);
    assert(g_close_calls==1 && g_read_calls>=2);
    reset_io(over_file,sizeof(over_file));
    assert(!ui_resolution_read("over-64k",&width,&height));
    assert(g_close_calls==1);
    puts("PASS resolution bounds: complete 64 KiB accepted and 64 KiB-plus-one rejected");
}

static void test_load_atomicity(void) {
    reset_io((const unsigned char*)basic_file,(DWORD)strlen(basic_file));
    g_ui_screen_w=3440; g_ui_screen_h=1440; g_ui_auto_resolution=1;
    set_path("C:\\Games\\Refuge\\prm-uifix.dll");
    ui_resolution_load();
    assert_dims(1920,1080);
    assert(g_log_count==1 && strstr(g_last_log,"detected")!=0);
    reset_io((const unsigned char*)invalid_file,(DWORD)strlen(invalid_file));
    g_ui_screen_w=3440; g_ui_screen_h=1440; g_ui_auto_resolution=1;
    ui_resolution_load();
    assert_dims(3440,1440);
    assert(g_log_count==1 && strstr(g_last_log,"using INI")!=0);
    reset_io((const unsigned char*)basic_file,(DWORD)strlen(basic_file));
    g_ui_screen_w=3440; g_ui_screen_h=1440; g_ui_auto_resolution=0;
    ui_resolution_load();
    assert_dims(3440,1440);
    assert(g_open_calls==0 && g_read_calls==0 && g_close_calls==0);
    assert(g_log_count==1 && strstr(g_last_log,"manual INI")!=0);
    reset_io((const unsigned char*)basic_file,(DWORD)strlen(basic_file));
    g_ui_screen_w=3440; g_ui_screen_h=1440; g_ui_auto_resolution=1;
    g_open_fail=1;
    ui_resolution_load();
    assert_dims(3440,1440);
    assert(g_close_calls==0);
    puts("PASS resolution load: valid pair commits together; invalid/open failure and manual mode preserve INI fallback");
}
'''


def main() -> None:
    actual_decl = ""
    actual_test = 'static void test_actual_option_info(void) {}\n'
    if len(sys.argv) > 1:
        actual = Path(sys.argv[1]).read_bytes()
        if len(actual) <= 65536:
            expected_width, expected_height = expected_generated_resolution(actual)
            actual_decl = f"static const unsigned char actual_option_info[] = {{{c_hex(actual)}}};\n"
            actual_test = r'''
static void test_actual_option_info(void) {
    LONG width=1,height=2;
    reset_io(actual_option_info,(DWORD)sizeof(actual_option_info));
    assert(ui_resolution_read("savedata\\OptionInfo.lua",&width,&height));
    assert(width==EXPECTED_WIDTH && height==EXPECTED_HEIGHT);
    assert(g_open_calls==1 && g_close_calls==1);
    puts("PASS resolution I/O real fixture: savedata/OptionInfo.lua read through production helper");
}
'''.replace("EXPECTED_WIDTH", str(expected_width)).replace("EXPECTED_HEIGHT", str(expected_height))
        else:
            actual_test = 'static void test_actual_option_info(void) { puts("SKIP resolution I/O real fixture: file exceeds production bound"); }\n'

    source = "\n".join((PREFIX, RESOLUTION_HEADER, FUNCTIONS, actual_decl,
                          TESTS, actual_test,
                          r'''
int main(void) {
    test_paths();
    test_read_failures();
    test_limits();
    test_load_atomicity();
    test_actual_option_info();
    return 0;
}
'''))
    with tempfile.TemporaryDirectory(prefix="prm-resolution-io-") as name:
        directory = Path(name)
        (directory / "ui_resolution.h").write_text(RESOLUTION_HEADER)
        c_file = directory / "resolution_io.c"
        binary = directory / "resolution_io"
        c_file.write_text(source)
        compiler = shlex.split(os.environ.get("CC", "clang"))
        command = compiler + [
            "-m32", "-std=c11", "-O1", "-g", "-Wall", "-Wextra", "-Werror",
            "-fsanitize=address,undefined", "-fno-omit-frame-pointer",
            str(c_file), "-o", str(binary),
        ]
        subprocess.run(command, check=True)
        env = os.environ.copy()
        env.setdefault("ASAN_OPTIONS", "detect_leaks=0:halt_on_error=1")
        subprocess.run([str(binary)], check=True, env=env)


if __name__ == "__main__":
    main()
