# UI FIX 1.0.1 development validation

GitHub release 1.0 remains available at
https://github.com/TheThag/ReturntoMorrocUIScaling/releases/tag/v1.0.
This development build addresses the two issues reported during its preparation:
confirmation-dialog buttons and character hover names visible through the map.
The new changes still require an in-game check.

## Confirmation dialogs

The client constructs UIMessageBox and UIMessageBoxAutoreturn through 5F8C40 and
5F8E10 and registers them in UIWindowMgr list +174. Their shared native hit method
B217C0 tests the window rectangle and recurses into child controls. Previously,
the naming heuristic rejected these classes, leaving their clicks vulnerable to
the underlying window's inverse transform.

The generic admission fallback now requires primary, nonvirtual UIFrameWnd and
UIWindow bases. The native RTTI audit identifies eight newly admitted framed
classes. Direct UIWindow descendants include actor gauges and raw bitmap controls;
those keep their existing policies. The RTTI fixture exercises actual admission,
malformed metadata, class-independent dialog names and live-vtable identity. Its
modal-input case uses different transforms for overlapping windows, verifies the
modal's native child-button coordinates, and restores the underlying owner after
the modal disappears or becomes stale.

## Fullscreen map

The existing map renderer records same-frame, same-thread visual occlusion only
after the native draw executes. Exact identity, visibility and fullscreen bounds
are revalidated before suppressing a later character-name bitmap/background.
Names before the map draw remain part of the normal draw order. The marker cannot
carry into another frame or survive a hidden/replaced map.

The world ray, character movement correction, UI hit selection and map-region
input are unchanged by this rendering correction. Tests cover both horizontal
and vertical name classes, bitmap/background suppression, draw order, frame and
thread boundaries, map closure, geometry/vtable changes, disabled scaling and
unrelated windows.

## Verification scope

All 22 host harnesses pass. They execute production C functions and native assembly bridges
with 32-bit fixtures and sanitizer coverage. They do not launch the game. Native
hook checks are run against PRM.exe SHA256
`5b3fbd6b63d0e409dd0dbea0bcb389bab61d8e37a36855fe925a0a2310ea4d9b`.
The executable is not modified. Source/build input hashes are in SHA256SUMS;
local test output is kept under evidence/modal-map-fix outside the game folder.

The installed test DLL preserves the INI, including the Shift+P overlay binding,
blank optional shortcuts and the user's live scale/filter preferences.
The published 1.0 tag and ZIP retain their original tested source and binary.

Test DLL: 223744 bytes, PE32/i386, 185 exact WinMM exports, no static
imports, IAT or delay imports. SHA256:

`a963f1e7993ac52a659e4f56463ded3d93ced9d5ae1ee74dc9772844a3063fa5`
