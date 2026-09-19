# UI FIX validation

## World effects and additional UI roots (1.0.1-dev)

The user confirmed the preceding actor health/cast correction and reported a
misplaced summon flash that aligns correctly when UI scaling is disabled.
The primary renderer now requires exact native UI ownership before scaling a
draw. Geometry fallback can no longer transform world effects or supply their
mouse regions. Explicit legacy mode remains available.

The regression harness reproduces the old erroneous white-quad displacement
and verifies unchanged unowned vertices at 100%, 133%, 150%, 200% and 300%,
with matching groups and ScaleUnmatched both enabled and disabled. It checks
identical owned geometry still scales, record expiry/reuse, and stale-group
input isolation. Additional checks cover newly admitted merchant buy/sell
signs and the quest tracker, with actor attachment, screen fitting and inverse
click coordinates. Existing actor gauges, maps, tooltips and chat-room titles
retain their regression coverage.

Native evidence was checked against PRM.exe SHA256
`7e96f64968558b88d6fe7d4bdc7a12a15231ee30f942159babe54a9c99b1cc90`.
The exact summon-effect draw has not been captured; the false UI classification
is reproduced from production code and fits the user's scaling-off comparison.
In-game verification of this new correction remains pending. Evidence is under
`evidence/world-effects-fix`; installation preserves the live INI and executable.
The public release remains unchanged.

All 24 host harnesses and native verification pass. Test DLL: 230400
bytes, PE32/i386, 185 exact WinMM exports, no static imports/IAT/delay imports.
SHA256: `8d2ad825dcc83210644285d42e5c987d76613f682974a0a8dc1ac3f6685d45b8`.

## Actor combat UI test build (1.0.1-dev)

The development build adds independent bitmap ownership for other players'
health gauges, monster health gauges, and actor cast bars. They retain their
live native center while moving or resizing, at every configured scale.
UIPcGage children inside party panels keep their parent window's transform.
Actor text now scales around its native top-center attachment; chat-room
titles retain their bottom-pointer attachment, and tooltip identities retain
their existing placement rules.

All 24 host harnesses pass. The added movement cases cover 100%, 133%, 150%,
165%, 175%, and 200%; independent actors, queued transforms, odd dimensions,
viewport edges, and passive mouse behavior. The RTTI fixture distinguishes
actor roots from party-panel child gauges and keeps unrelated controls excluded.
Native hook/layout verification uses the current installed executable SHA256
`7e96f64968558b88d6fe7d4bdc7a12a15231ee30f942159babe54a9c99b1cc90`.
The executable is not modified. Test evidence is under
`evidence/actor-bars-fix` outside the game folder.

The user confirmed other actors' health/cast bars and spell names were fixed.
The public 1.0 release remains unchanged. The local test installation
preserves the existing INI, including the user's scale and shortcuts.

Test DLL: 230400 bytes, PE32/i386, 185 exact WinMM exports, no static imports,
IAT or delay imports. SHA256:
`a5695520b82ae8ce4900a9e684bcc31da9c22cad2f6e61444d70cb4cbc27d585`.

## Released 1.0 baseline

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
