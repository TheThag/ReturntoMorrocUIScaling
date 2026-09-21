#!/usr/bin/env python3
"""Execute the production UI draw adapters with the native i386 stack ABI."""
from pathlib import Path
import subprocess,tempfile
root=Path(__file__).resolve().parent
s=(root/'vtrace_thunks.S').read_text().split('/* Native queue draw callsites',1)[1]
s=s[s.index('.text'):].replace('_native_DrawPrimitive@24','dp').replace('_native_DrawIndexedPrimitive@32','dip')
s+=r'''
.text
.globl _start
_start:
 movl %esp,saved
 movl $primitive,%ebx
 movl $123,%ecx
 pushl $6
 pushl $5
 pushl $4
 pushl $3
 call _native_dp_thunk
 cmpl saved,%esp
 jne fail
 cmpl $77,%eax
 jne fail
 movl $123,%ecx
 pushl $8
 pushl $7
 pushl $6
 pushl $5
 pushl $4
 pushl $3
 call _native_dip_thunk
 cmpl saved,%esp
 jne fail
 cmpl $88,%eax
 jne fail
 movl $1,%eax
 xorl %ebx,%ebx
 int $0x80
dp:
 cmpl $123,4(%esp)
 jne fail
 cmpl $2,8(%esp)
 jne fail
 cmpl $3,12(%esp)
 jne fail
 cmpl $4,16(%esp)
 jne fail
 cmpl $5,20(%esp)
 jne fail
 cmpl $6,24(%esp)
 jne fail
 movl $77,%eax
 ret $24
dip:
 cmpl $123,4(%esp)
 jne fail
 cmpl $2,8(%esp)
 jne fail
 cmpl $3,12(%esp)
 jne fail
 cmpl $4,16(%esp)
 jne fail
 cmpl $5,20(%esp)
 jne fail
 cmpl $6,24(%esp)
 jne fail
 cmpl $7,28(%esp)
 jne fail
 cmpl $8,32(%esp)
 jne fail
 movl $88,%eax
 ret $32
fail:
 movl $1,%eax
 movl $1,%ebx
 int $0x80
.data
saved: .long 0
primitive: .zero 36
.long 2
'''
with tempfile.TemporaryDirectory() as d:
 p=Path(d);(p/'t.S').write_text(s)
 subprocess.run(['clang','-target','i386-linux-gnu','-c',str(p/'t.S'),'-o',str(p/'t.o')],check=True)
 subprocess.run(['ld.lld','-m','elf_i386','-e','_start',str(p/'t.o'),'-o',str(p/'t')],check=True)
 subprocess.run([str(p/'t')],check=True)
print('PASS: production native draw thunks, all DP/DIP arguments, stack cleanup and HRESULT forwarding')
