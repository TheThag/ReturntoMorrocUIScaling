.text
.globl _vtrace_slot_0
_vtrace_slot_0:
  pushl $0
  jmp _vtrace_enter_common
.globl _vtrace_slot_1
_vtrace_slot_1:
  pushl $1
  jmp _vtrace_enter_common
.globl _vtrace_slot_2
_vtrace_slot_2:
  pushl $2
  jmp _vtrace_enter_common
.globl _vtrace_slot_3
_vtrace_slot_3:
  pushl $3
  jmp _vtrace_enter_common
.globl _vtrace_slot_4
_vtrace_slot_4:
  pushl $4
  jmp _vtrace_enter_common
.globl _vtrace_slot_5
_vtrace_slot_5:
  pushl $5
  jmp _vtrace_enter_common
.globl _vtrace_slot_6
_vtrace_slot_6:
  pushl $6
  jmp _vtrace_enter_common
.globl _vtrace_slot_7
_vtrace_slot_7:
  pushl $7
  jmp _vtrace_enter_common
.globl _vtrace_slot_8
_vtrace_slot_8:
  pushl $8
  jmp _vtrace_enter_common
.globl _vtrace_slot_9
_vtrace_slot_9:
  pushl $9
  jmp _vtrace_enter_common
.globl _vtrace_slot_10
_vtrace_slot_10:
  pushl $10
  jmp _vtrace_enter_common
.globl _vtrace_slot_11
_vtrace_slot_11:
  pushl $11
  jmp _vtrace_enter_common
.globl _vtrace_slot_12
_vtrace_slot_12:
  pushl $12
  jmp _vtrace_enter_common
.globl _vtrace_slot_13
_vtrace_slot_13:
  pushl $13
  jmp _vtrace_enter_common
.globl _vtrace_slot_14
_vtrace_slot_14:
  pushl $14
  jmp _vtrace_enter_common
.globl _vtrace_slot_15
_vtrace_slot_15:
  pushl $15
  jmp _vtrace_enter_common
.globl _vtrace_slot_16
_vtrace_slot_16:
  pushl $16
  jmp _vtrace_enter_common
.globl _vtrace_slot_17
_vtrace_slot_17:
  pushl $17
  jmp _vtrace_enter_common
.globl _vtrace_slot_18
_vtrace_slot_18:
  pushl $18
  jmp _vtrace_enter_common
.globl _vtrace_slot_19
_vtrace_slot_19:
  pushl $19
  jmp _vtrace_enter_common
.globl _vtrace_slot_20
_vtrace_slot_20:
  pushl $20
  jmp _vtrace_enter_common
.globl _vtrace_slot_21
_vtrace_slot_21:
  pushl $21
  jmp _vtrace_enter_common
.globl _vtrace_slot_22
_vtrace_slot_22:
  pushl $22
  jmp _vtrace_enter_common
.globl _vtrace_slot_23
_vtrace_slot_23:
  pushl $23
  jmp _vtrace_enter_common
.globl _vtrace_slot_24
_vtrace_slot_24:
  pushl $24
  jmp _vtrace_enter_common
.globl _vtrace_slot_25
_vtrace_slot_25:
  pushl $25
  jmp _vtrace_enter_common
.globl _vtrace_slot_26
_vtrace_slot_26:
  pushl $26
  jmp _vtrace_enter_common
.globl _vtrace_slot_27
_vtrace_slot_27:
  pushl $27
  jmp _vtrace_enter_common
.globl _vtrace_slot_28
_vtrace_slot_28:
  pushl $28
  jmp _vtrace_enter_common
.globl _vtrace_slot_29
_vtrace_slot_29:
  pushl $29
  jmp _vtrace_enter_common
.globl _vtrace_slot_30
_vtrace_slot_30:
  pushl $30
  jmp _vtrace_enter_common
.globl _vtrace_slot_31
_vtrace_slot_31:
  pushl $31
  jmp _vtrace_enter_common
.globl _vtrace_slot_32
_vtrace_slot_32:
  pushl $32
  jmp _vtrace_enter_common
.globl _vtrace_slot_33
_vtrace_slot_33:
  pushl $33
  jmp _vtrace_enter_common
.globl _vtrace_slot_34
_vtrace_slot_34:
  pushl $34
  jmp _vtrace_enter_common
.globl _vtrace_slot_35
_vtrace_slot_35:
  pushl $35
  jmp _vtrace_enter_common
.globl _vtrace_slot_36
_vtrace_slot_36:
  pushl $36
  jmp _vtrace_enter_common
.globl _vtrace_slot_37
_vtrace_slot_37:
  pushl $37
  jmp _vtrace_enter_common
.globl _vtrace_slot_38
_vtrace_slot_38:
  pushl $38
  jmp _vtrace_enter_common
.globl _vtrace_slot_39
_vtrace_slot_39:
  pushl $39
  jmp _vtrace_enter_common
.globl _vtrace_enter_common
_vtrace_enter_common:
  popl _g_vtrace_asm_slot
  movl %ecx, _g_vtrace_asm_self
  movl (%esp), %eax
  movl %eax, _g_vtrace_asm_ret
  pushfl
  pushal
  call _vtrace_enter_c@0
  popal
  popfl
  movl $_vtrace_leave_common, (%esp)
  jmp *_g_vtrace_asm_jump

.globl _vtrace_leave_common
_vtrace_leave_common:
  pushfl
  pushal
  call _vtrace_leave_c@0
  popal
  popfl
  jmp *_g_vtrace_asm_return

.globl _vtrace_submit0_thunk
_vtrace_submit0_thunk:
  pushfl
  pushal
  call _vtrace_note_submit0@0
  popal
  popfl
  pushl %ebp
  movl %esp, %ebp
  pushl %esi
  movl 0x24(%ecx), %esi
  jmp *_g_vtrace_submit0_continue

.globl _vtrace_submit1_thunk
_vtrace_submit1_thunk:
  pushfl
  pushal
  call _vtrace_note_submit1@0
  popal
  popfl
  jmp *_g_vtrace_submit1_target

.globl _vtrace_submit2_thunk
_vtrace_submit2_thunk:
  pushfl
  pushal
  call _vtrace_note_submit2@0
  popal
  popfl
  pushl %ebp
  movl %esp, %ebp
  subl $0x38, %esp
  jmp *_g_vtrace_submit2_continue

/* Phase 2J: real UIWindow ownership at the three deferred-submit helpers. */
.globl _owner_submit0_thunk
_owner_submit0_thunk:
  pushfl
  pushal
  movl 24(%esp), %eax
  movl 40(%esp), %ebx
  movl 44(%esp), %ecx
  movl 48(%esp), %edx
  movl 52(%esp), %esi
  pushl %esi
  pushl %edx
  pushl %ecx
  pushl %ebx
  pushl %eax
  call _owner_submit_note_a@20
  popal
  popfl
  pushl %ebp
  movl %esp, %ebp
  pushl %esi
  movl 0x24(%ecx), %esi
  jmp *_g_owner_submit0_continue

.globl _owner_submit1_thunk
_owner_submit1_thunk:
  pushfl
  pushal
  movl 24(%esp), %eax
  movl 40(%esp), %ebx
  movl 44(%esp), %ecx
  movl 48(%esp), %edx
  movl 52(%esp), %esi
  movl 56(%esp), %edi
  pushl %edi
  pushl %esi
  pushl %edx
  pushl %ecx
  pushl %ebx
  pushl %eax
  call _owner_submit_note_b@24
  popal
  popfl
  jmp *_g_owner_submit1_target

.globl _owner_submit2_thunk
_owner_submit2_thunk:
  pushfl
  pushal
  movl 24(%esp), %eax
  movl 40(%esp), %ebx
  movl 44(%esp), %ecx
  movl 48(%esp), %edx
  movl 52(%esp), %esi
  movl 56(%esp), %edi
  pushl %edi
  pushl %esi
  pushl %edx
  pushl %ecx
  pushl %ebx
  pushl %eax
  call _owner_submit_note_c@24
  popal
  popfl
  pushl %ebp
  movl %esp, %ebp
  subl $0x38, %esp
  jmp *_g_owner_submit2_continue

/* Phase 2V: manager already pushed x,y,width,height,color. Replace precisely
 * the indirect bitmap CALL and following EBX restore (six bytes). */
.globl _owner_bitmap_primary_thunk
_owner_bitmap_primary_thunk:
  pushl 0x28(%ebx)
  pushl %ecx
  pushl %edi
  call _owner_bitmap_draw_c@32
  movl -0x24(%ebp), %ebx
  jmp *_g_owner_bitmap_primary_continue

.globl _owner_bitmap_alternate_thunk
_owner_bitmap_alternate_thunk:
  pushl 0x0c(%ebx)
  pushl %ecx
  pushl %edi
  call _owner_bitmap_draw_c@32
  movl -0x24(%ebp), %ebx
  jmp *_g_owner_bitmap_alternate_continue
