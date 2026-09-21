#!/usr/bin/env python3
"""Run production read-only device observations against live and invalid fixtures."""
from pathlib import Path
import subprocess
import tempfile
from test_input import extract_function
source=Path(__file__).with_name('prm_uifix.c').read_text()
code=r'''
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <assert.h>
typedef uint32_t DWORD;
typedef uintptr_t ULONG_PTR;
typedef unsigned char BYTE;
static BYTE exe[0xa4ca5], renderer[0x78];
static void *device, *table[36], *table2[36];
static void *g_exe=exe;
static DWORD g_exe_size=sizeof(exe);
static int g_logging=1;
static void *g_diag_queue_renderer,*g_diag_queue_device;
static void **g_diag_queue_vt;
static DWORD g_diag_queue_changes;
static int mem_readable(const void *p,DWORD n) {
 uintptr_t a=(uintptr_t)p;
 return p && a!=1 && n>0;
}
static char logs[10000];
static void log_line(const char *s) {strcat(logs,s); strcat(logs,"\n");}
static void s_append(char *s,unsigned n,const char *v) {strncat(s,v,n-strlen(s)-1);}
static void s_append_uint(char *s,unsigned n,DWORD v) {char b[32];snprintf(b,sizeof(b),"%u",v);s_append(s,n,b);}
static void s_append_hex8(char *s,unsigned n,DWORD v) {char b[32];snprintf(b,sizeof(b),"%08x",v);s_append(s,n,b);}
static DWORD ptr_to_rva(void *p) {(void)p;return 0xffffffff;}
'''
names=['BeginScene','EndScene','DrawPrimitive','DrawIndexedPrimitive','DrawPrimitiveStrided','DrawIndexedPrimitiveStrided','DrawPrimitiveVB','DrawIndexedPrimitiveVB','SetTexture']
for n in names: code+=f'static void hook_{n}(void) {{}}\n'
for n in ['diagnostic_observe_renderer','diagnostic_dump_vtable']: code+=extract_function(source,n)+'\n'
code+=r'''
int main(void) {
 exe[0xa4ca2]=0x8b;exe[0xa4ca3]=0x4f;exe[0xa4ca4]=0x74;
 device=table; *(void**)(renderer+0x74)=&device;
 diagnostic_observe_renderer(renderer);
 assert(g_diag_queue_changes==1 && g_diag_queue_vt==table);
 diagnostic_observe_renderer(renderer);assert(g_diag_queue_changes==1);
 device=table2;diagnostic_observe_renderer(renderer);assert(g_diag_queue_changes==2 && g_diag_queue_vt==table2);
 g_logging=0;device=table;diagnostic_observe_renderer(renderer);assert(g_diag_queue_changes==2);
 g_logging=1;exe[0xa4ca4]=0;diagnostic_observe_renderer(renderer);assert(g_diag_queue_changes==2);
 exe[0xa4ca4]=0x74;diagnostic_observe_renderer((void*)1);assert(g_diag_queue_changes==2);
 table[25]=(void*)hook_DrawPrimitive;
 diagnostic_dump_vtable("test",table);
 assert(strstr(logs,"intact=1") && strstr(logs,"intact=0"));
 assert(table[25]==(void*)hook_DrawPrimitive && table[26]==0);
 logs[0]=0;diagnostic_dump_vtable("bad",(void**)1);assert(strstr(logs,"unreadable"));
 return 0;
}
'''
with tempfile.TemporaryDirectory() as d:
 p=Path(d)/'test.c';p.write_text(code);exe=Path(d)/'test'
 subprocess.run(['clang','-m32','-fsanitize=address,undefined',str(p),'-o',str(exe)],check=True)
 subprocess.run([str(exe)],check=True)
print('PASS: native device/vtable changes, disabled logging, invalid signature/pointers, read-only hook-slot checks')
