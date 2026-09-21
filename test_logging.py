#!/usr/bin/env python3
"""Exercise automatic logging timing, disabled mode and empty-capture completion."""
import subprocess
import tempfile
from pathlib import Path
from test_input import extract_function
source = Path(__file__).with_name("prm_uifix.c").read_text()
fixture = r'''#include <stdint.h>
#include <assert.h>
typedef uint32_t DWORD;
static int g_logging, g_logging_started, g_capture_active;
static DWORD g_logging_last_tick, now, deadline;
static int snapshots, groups, starts;
static DWORD tick(void) { return now; }
static DWORD (*g_GetTickCount)(void)=tick;
#define UIHK_DIAGNOSTICS 0
#define UIHK_GROUPS 1
#define UIHK_TRACE 2
static DWORD queued;
static void diagnostic_dump_devices(void) {}
static void log_line(const char *s) {(void)s;}
static void ui_hotkeys_queue(DWORD mask) {queued|=mask;}
static void maybe_finish_capture(void) {if(g_capture_active && (int32_t)(now-deadline)>=0) g_capture_active=0;}
static void maybe_dump_owner_windows(void) {assert(queued&1); queued&=~1; ++snapshots;}
static void maybe_dump_ui_groups(void) {assert(queued&2); queued&=~2; ++groups;}
static void maybe_start_capture(void) {assert(queued&4); queued&=~4; ++starts; g_capture_active=1; deadline=now+2000;}
'''
fixture += extract_function(source, "automatic_logging_poll")
fixture += r'''
int main(void) {
 automatic_logging_poll(); assert(starts==0);
 g_logging=1; automatic_logging_poll(); assert(starts==1 && snapshots==1 && groups==1 && !queued);
 now=1999; automatic_logging_poll(); assert(g_capture_active && starts==1);
 now=2000; automatic_logging_poll(); assert(!g_capture_active && starts==1);
 now=9999; automatic_logging_poll(); assert(starts==1);
 now=10000; automatic_logging_poll(); assert(starts==2);
 now=20000; g_capture_active=1; deadline=22000; automatic_logging_poll(); assert(starts==2);
 now=22000; automatic_logging_poll(); assert(starts==3);
 g_capture_active=0; g_logging_last_tick=UINT32_MAX-4999; now=5000;
 automatic_logging_poll(); assert(starts==4);
 g_logging=0; now+=10000; automatic_logging_poll(); assert(starts==4);
 g_logging=1; g_GetTickCount=0; automatic_logging_poll(); assert(starts==4);
 return 0;
}
'''
with tempfile.TemporaryDirectory() as d:
    c=Path(d)/"logging.c"; c.write_text(fixture)
    exe=Path(d)/"logging"
    subprocess.run(["clang", "-Wall", "-Werror", str(c), "-o", str(exe)], check=True)
    subprocess.run([str(exe)], check=True)
print("Automatic logging checks passed")
