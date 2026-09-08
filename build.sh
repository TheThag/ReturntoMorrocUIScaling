#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
CLANG="${CLANG:-clang}"
LLD="${LLD:-lld-link}"

"$CLANG" \
  -target i686-pc-windows-msvc \
  -O2 -fno-omit-frame-pointer -ffreestanding -fno-builtin -fno-stack-protector \
  -fno-exceptions -fno-unwind-tables -fno-asynchronous-unwind-tables \
  -c "$ROOT/prm_uifix.c" -o "$ROOT/prm_uifix.obj"

"$CLANG" -target i686-pc-windows-msvc -c "$ROOT/winmm_forwarders.S" -o "$ROOT/winmm_forwarders.obj"
"$CLANG" -target i686-pc-windows-msvc -c "$ROOT/vtrace_thunks.S" -o "$ROOT/vtrace_thunks.obj"

"$LLD" \
  /dll /nodefaultlib /machine:x86 /safeseh:no '/entry:DllMain@12' \
  "/def:$ROOT/winmm.def" \
  "/out:$ROOT/winmm.dll" \
  "$ROOT/prm_uifix.obj" "$ROOT/winmm_forwarders.obj" "$ROOT/vtrace_thunks.obj"

file "$ROOT/winmm.dll"
