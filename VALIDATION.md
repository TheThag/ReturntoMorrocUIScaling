# UI FIX 1.0 validation

This refreshed 1.0 release adds startup resolution detection and addresses the
confirmation-dialog, fullscreen-map hover-name, and related UI ownership issues.
The release was user-confirmed under Linux/Wine at 200% scaling.

## Installation

Close the game, preserve any existing `winmm.dll` and `prm-ui-fix.ini`, and
extract the release `winmm.dll` and `prm-ui-fix.ini` beside `PRM.exe`. Start the
game after installation; the proxy creates `prm-ui-fix.log` in the same folder.
For Wine or Lutris, set `WINEDLLOVERRIDES=winmm=n,b` while preserving any other
overrides. Remove the proxy and restore the preserved files to uninstall.

Windows and dgVoodoo with the DirectX 11 renderer are untested. The validation
below covers the supported Linux/Wine test environment and the identified
2020-09-02 client executable.

## Automatic resolution

The default `UI.AutoDetectResolution=1` loads the literal WIDTH/HEIGHT pair from
the installed game's `savedata/OptionInfo.lua`. Both values replace the manual
INI dimensions together, before any renderer or input hook is installed. Invalid
or unavailable data leaves the INI fallback intact; `AutoDetectResolution=0`
selects manual dimensions without opening the file. The startup log reports the
selected source and effective dimensions. Resolution changes require a restart.

The parser and file-loader harnesses pass with generated 1080p, 1440p, 4K and
boundary-size fixtures, and with the real saved file reporting 3440x1440. They
cover exact keys, comments/strings, malformed and truncated values, duplicates,
read failures, short reads, the 64 KiB file bound and handle cleanup. Tests run
without a game installation; an optional path adds a real-file check. The loader
harness executes the production functions with 32-bit ASan/UBSan and Win32 stubs.
Manual startup verification under Linux/Wine confirmed the log selecting
3440x1440 with `AutoDetectResolution=1`, `SharpFilter=0`, and 200% scaling.

`UI.SharpFilter=0` remains the default in both source and the distributed INI,
so crisp point sampling is off. Existing overlay settings and shortcuts retain
their behavior.

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

All 24 host harnesses pass. They execute production C functions and native assembly bridges,
including 32-bit fixtures with sanitizer coverage. They do not launch the game. Native
hook checks are run against PRM.exe SHA256
`5b3fbd6b63d0e409dd0dbea0bcb389bab61d8e37a36855fe925a0a2310ea4d9b`.
The executable is not modified. Source/build input hashes are in SHA256SUMS;
local test output is kept under evidence/auto-resolution and
evidence/release-1.0-refresh outside the game folder.

The test installation adds `AutoDetectResolution=1` and keeps `SharpFilter=0`.
Other INI values, including Shift+P, blank optional shortcuts and the user's
200% scale, are preserved. The refreshed 1.0 release binary uses the same
behavioral code as the tested build; the release rebuild changes version labels
only.

Release DLL: `230400` bytes, PE32/i386, 185 exact WinMM exports, no
static imports, IAT or delay imports. SHA256:

`c997e4430e8415420a85ab24052f600cadf792ee021aa83178c2b92bf8cf777e`
