from pathlib import Path
import subprocess,tempfile
s=Path('vtrace_thunks.S').read_text().split('/* Cooldown producers:',1)[1].split('/* Native queue draw callsites',1)[0]
s=s[s.index('.globl'):].replace('_owner_cooldown_build_c@40','bridge')
s='.text\n'+s+'\n.globl _start\n_start:\n subl $2048,%esp\n movl %esp,%ebp\n addl $2048,%ebp\n movl $456,-0x768(%ebp)\n movl $789,-0x774(%ebp)\n movl %esp,saved\n'
for name,owner in [('item',456),('skill',789),('buff',0)]:
 s+=f' movl ${owner},expected\n movl $123,%ecx\n'
 for i in range(8,0,-1):s+=f' pushl ${i}\n'
 s+=f' call _owner_cooldown_{name}_thunk\n cmpl saved,%esp\n jne fail\n cmpl $99,%eax\n jne fail\n'
s+=' movl $1,%eax\n xorl %ebx,%ebx\n int $0x80\nbridge:\n cmpl $123,4(%esp)\n jne fail\n movl expected,%eax\n cmpl %eax,8(%esp)\n jne fail\n'
for i in range(1,9):s+=f' cmpl ${i},{8+i*4}(%esp)\n jne fail\n'
s+=' movl $99,%eax\n ret $40\nfail:\n movl $1,%eax\n movl $1,%ebx\n int $0x80\n.data\nsaved: .long 0\nexpected: .long 0\n'
with tempfile.TemporaryDirectory() as d:
 p=Path(d);(p/'t.S').write_text(s)
 subprocess.run(['clang','-target','i386-linux-gnu','-c',str(p/'t.S'),'-o',str(p/'t.o')],check=True)
 subprocess.run(['ld.lld','-m','elf_i386','-e','_start',str(p/'t.o'),'-o',str(p/'t')],check=True)
 subprocess.run([str(p/'t')],check=True)
print('PASS cooldown native adapters: owner frame offsets, renderer, eight arguments, return value and exact stack cleanup')
