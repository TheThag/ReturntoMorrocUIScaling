# Phase 3F validation

The user confirmed Phase 3E's tooltip reentry, hotbar hover and chat resize
fixes, then reported misplaced explanations on the Alt+V menu buttons.
This build corrects tooltip placement when native clipping happens before
our source transform. In-game confirmation of this change is pending.

## Evidence and implementation

The Phase 3E F8 log places UIMenuIconWnd at native (-74,1608), size 220x197,
with anchor (0,1440), scale 200% and offset (244,-938). It displays correctly
at (96,838)..(536,1232). Its generic tooltip has the correct retained source,
but its cached origin is clamped to (-3,1422) by the native factory. Transforming
that clamped point places the tooltip at (238,466), above its menu.

Native 628560..6285AE clips the requested coordinates independently into
[-3, viewport dimension - popup dimension + 3]. The existing clock bridge at
6284A2 now captures the original arguments from factory EBP+0C/+10. Rendering
transforms this requested origin through the retained source, compensates for
the actual cache origin, then applies the existing screen-fitting policy.
This applies to any owned source using the ordinary tooltip factory.

The native factory, bitmap coordinates and clock result are preserved. The
bridge forwards controller/x/y with stdcall 12-byte cleanup. The source and
requested origin survive pointer exit and update on each nonempty factory call,
including two calls in the same clock tick. The accepted buff, actor speech,
character-info, input, chat and settings paths retain their existing behavior.

## Verification

All 20 host harnesses pass. The extended bounds fixture models the logged
menu transform with a requested origin (-68,1615), whose expected displayed
origin is (108,852). It checks the actual queued bitmap output after native
clipping. That requested origin is a regression example, not a value captured
by the old runtime log. Phase 3F now logs the requested coordinates too.

Additional rendering cases cover all four native clipping edges and an
unclipped origin at 133%, 150% and 200%, followed by final screen fitting.
Lifetime checks cover changed requested coordinates within one clock tick and
retention after pointer exit. The real i386 assembly fixture checks EBP argument
forwarding, EAX return, registers, stack cleanup and continuations. The existing
map/minimap, connected windows, bounds, drag/capture, input, cursor, filtering,
presentation, settings, owner lifetime, buff and chat tests also pass.

Native verification passes all 21 direct calls, 3 bitmap/background spans,
3 input/refresh spans, 2 offscreen returns, the central mouse return and layout
evidence, including the factory frame and argument loads. The runtime auditor
accepts 3E and 3F and passes synthetic latest-run, missing-snapshot and invalid
bounds/counter checks. These tests use native fixtures and do not launch PRM.

## Artifact and installation

DLL: 211968 bytes, PE32/i386, exactly 185 WinMM exports,
no static imports, IAT or delay imports. SHA256:

```
d8fd8b5e190a5dc9145d7b672d0c2f25e60fb73ed5bab90690cd1de55e13dd75
```

PRM.exe remains unchanged, SHA256
`5b3fbd6b63d0e409dd0dbea0bcb389bab61d8e37a36855fe925a0a2310ea4d9b`.
The accepted ui_settings.h is unchanged. The supplied INI remains 150%; the
installation replaces only winmm.dll and preserves the live INI at 200% with
native smoothing and KeepOnScreen enabled. Build/source hashes are recorded in
SHA256SUMS. Evidence and rollback files stay in evidence/phase3f-work; the
matching source/build is archived in releases/phase3f.

Restart and hover the Alt+V menu buttons, including after moving the connected
Basic Info/menu block. Press F8 if placement is still wrong. Wait for the user's
result after handoff; do not poll for manual-test completion.
