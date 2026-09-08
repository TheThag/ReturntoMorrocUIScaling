#!/usr/bin/env python3
"""Execute bitmap/background thunks in a freestanding Linux i386 harness.

Tests stack layout/cleanup, forwarding, EDI/EBP preservation, EBX restoration,
and continuation jumps. This does not launch PRM or validate Wine rendering.
"""
from pathlib import Path
import subprocess
import tempfile

root = Path(__file__).resolve().parent
production = (root / 'vtrace_thunks.S').read_text().split('/* Phase 2V:', 1)[1]
production = production[production.index('.globl _owner_bitmap_primary_thunk'):]
production = production.replace('_owner_bitmap_draw_c@32', 'bitmap_draw_stub')
production = production.replace('_owner_background_draw_c@24', 'background_draw_stub')
harness = r'''
.text
.globl _start
_start:
    movl %esp, %ebp
    subl $128, %esp
    movl %esp, expected_sp
    movl %ebp, expected_bp
    movl $0x12345678, -0x24(%ebp)
    movl $primary_continue, _g_owner_bitmap_primary_continue
    movl $alternate_continue, _g_owner_bitmap_alternate_continue
    movl $window_object, %edi
    movl $bitmap_object, %ecx
    movl $primary_vtable, %ebx
    pushl $0xabcdef01
    pushl $141
    pushl $280
    pushl $543
    pushl $987
    jmp _owner_bitmap_primary_thunk
primary_continue:
    call check_state
    movl $window_object, %edi
    movl $bitmap_object, %ecx
    movl $alternate_vtable, %ebx
    pushl $0xabcdef01
    pushl $141
    pushl $280
    pushl $543
    pushl $987
    jmp _owner_bitmap_alternate_thunk
alternate_continue:
    call check_state
    cmpl $2, native_calls
    jne fail
    movl $0x31415926, %esi
    pushl $0xaabbccdd
    pushl $106
    pushl $146
    pushl $171
    pushl $3246
    call _owner_background_thunk
    cmpl $3246, (%esp)
    jne fail
    cmpl $0xaabbccdd, 16(%esp)
    jne fail
    addl $20, %esp
    call check_state
    cmpl $0x31415926, %esi
    jne fail
    cmpl $1, background_calls
    jne fail
    movl $1, %eax
    xorl %ebx, %ebx
    int $0x80
check_state:
    cmpl $0x12345678, %ebx
    jne fail
    cmpl $window_object, %edi
    jne fail
    cmpl expected_bp, %ebp
    jne fail
    leal 4(%esp), %edx
    cmpl expected_sp, %edx
    jne fail
    cmpl $0x11223344, %eax
    jne fail
    ret
bitmap_draw_stub:
    cmpl $window_object, 4(%esp)
    jne fail
    cmpl $bitmap_object, 8(%esp)
    jne fail
    cmpl $native_bitmap, 12(%esp)
    jne fail
    cmpl $987, 16(%esp)
    jne fail
    cmpl $543, 20(%esp)
    jne fail
    cmpl $280, 24(%esp)
    jne fail
    cmpl $141, 28(%esp)
    jne fail
    cmpl $0xabcdef01, 32(%esp)
    jne fail
    movl %esp, %edx
    movl 8(%edx), %ecx
    pushl 32(%edx)
    pushl 28(%edx)
    pushl 24(%edx)
    pushl 20(%edx)
    pushl 16(%edx)
    call *12(%edx)
    ret $32
background_draw_stub:
    cmpl $window_object, 4(%esp)
    jne fail
    cmpl $3246, 8(%esp)
    jne fail
    cmpl $171, 12(%esp)
    jne fail
    cmpl $146, 16(%esp)
    jne fail
    cmpl $106, 20(%esp)
    jne fail
    cmpl $0xaabbccdd, 24(%esp)
    jne fail
    incl background_calls
    movl $0x11223344, %eax
    ret $24
native_bitmap:
    cmpl $bitmap_object, %ecx
    jne fail
    cmpl $987, 4(%esp)
    jne fail
    cmpl $543, 8(%esp)
    jne fail
    cmpl $280, 12(%esp)
    jne fail
    cmpl $141, 16(%esp)
    jne fail
    cmpl $0xabcdef01, 20(%esp)
    jne fail
    incl native_calls
    movl $0x11223344, %eax
    ret $20
fail:
    movl $1, %eax
    movl $1, %ebx
    int $0x80
.data
.p2align 2
expected_sp: .long 0
expected_bp: .long 0
native_calls: .long 0
background_calls: .long 0
_g_owner_bitmap_primary_continue: .long 0
_g_owner_bitmap_alternate_continue: .long 0
window_object: .long 0
bitmap_object: .long 0
primary_vtable:
    .zero 40
    .long native_bitmap
alternate_vtable:
    .zero 12
    .long native_bitmap
'''
with tempfile.TemporaryDirectory(prefix='prm-thunks-') as tmp:
    folder = Path(tmp)
    (folder / 'thunks.S').write_text('.text\n' + production + harness)
    subprocess.run(['clang', '-target', 'i386-linux-gnu', '-c', str(folder / 'thunks.S'), '-o', str(folder / 'thunks.o')], check=True)
    subprocess.run(['ld.lld', '-m', 'elf_i386', '-e', '_start', str(folder / 'thunks.o'), '-o', str(folder / 'thunks')], check=True)
    subprocess.run([str(folder / 'thunks')], check=True)
print('PASS actual bitmap/background thunks: i386 forwarding, native ret20, wrapper ret32/24, cdecl caller cleanup, stack/register restoration, both continuations')
