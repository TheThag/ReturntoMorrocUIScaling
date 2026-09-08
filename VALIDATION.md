# Phase 3B validation

The user accepted Phase 3A as "working well". Phase 3B implements the subsequent
requests to keep enlarged movable windows inside the screen and provide live
settings, plus the later tooltip and moving-bar reports. Its focused in-game
test is pending. Work is on `fix/ui-screen-bounds`;
public `main` still contains Phase 2Z.

## Artifact identity

| Artifact | SHA256 |
| --- | --- |
| `winmm.dll` | `73c64055d53b93178c8988a1ae2fbefb25c62b9058473edf85eacfdbbdd15d05` |
| Target `PRM.exe` | `5b3fbd6b63d0e409dd0dbea0bcb389bab61d8e37a36855fe925a0a2310ea4d9b` |
| `prm-ui-fix.ini` | `bea46a21132b93954950d0a433a217f10eb77265fb5287e1d5f791ce473966bb` |

The DLL is 194048 bytes, PE32/i386, with exactly 185 WinMM exports and no static
imports, IAT or delay imports. All 14 host harnesses passed in the final run. The INI
retains 3440×1440, 200%, native smoothing and unchanged font metrics. KeepOnScreen
defaults to enabled when absent. PRM.exe is unchanged on disk.

## Behavior and verification

Ordinary owned windows receive a persistent correction if their enlarged bounds
cross a screen edge. Their scale is reduced uniformly when needed to fit. The
same scale and offset pass through whole-bitmap queues, final drawing, input
regions, selected-owner hit tests and captured-child mapping. Native window
positions are never rewritten. Cursor-following descriptions also fit; accepted
world-attachment and native fullscreen policies remain intact.

The native Basic Info/Menu relationship is verified at 5FF205, 5FF237..248,
ACF733..73F and 606ADF. Their union receives one correction. Membership, object
identity, parentage, enabled state and IDs are checked, including the cached
same-frame path. Unknown neighboring windows keep independent corrections.

F2 opens a native settings panel owned by the game. Its separate message thread
publishes an atomic request; the render boundary applies it after any game
capture ends. Apply changes runtime settings. Save writes only the four relevant
UI keys. The original native click, capture, map, minimap, world-ray and cursor
hook locations are retained.

Local checks:

- `test_bounds.py`: enabled fitting at four corners, 125/133/150/175/200%, and
  720/1080/1440-high screens; oversized fitting, input round trips, persistent
  edge correction, inward movement, frozen queued scales/offsets, captured input,
  independent windows and disabled/world/native-size policies.
  It also exercises first-draw/revisited transient popups, a control-derived
  popup origin, hidden character-info caches, actor speech while UI is hovered,
  and the player gauge following ten successive native positions.
- `test_connected.py`: actual active manager-list traversal and native 32-bit
  objects, both Basic/Menu orders, five scales, whole-pair bounds and spacing,
  next-frame movement, missing/disabled/parented roots, wrong IDs and reused
  vtables. A cached-vtable regression was reproduced, fixed and rechecked.
- Existing bitmap, drag, native hit ownership, map, minimap, capture and present
  harnesses pass. Their baseline mode explicitly disables KeepOnScreen; the new
  enabled-feature fixtures cover the changed behavior. ASan/UBSan are used for
  the native object and ownership fixtures.
- `test_settings.py` exercises percentage validation, atomic requests, deferred
  commit, Apply without file writes, four-key Save and partial-save failures,
  F2 gating, coherent settings snapshots, stale queued closes and window
  lifecycle. Native UI structures and creation
  behavior are checked with the i386 stdcall ABI and ASan/UBSan, separately from
  actual Wine rendering.
- `test_hit.py` reproduces the old-position hover bug with a displayed-UI miss
  inside the native chat rectangle. The scoped native query rejects that ghost
  hit across stationary frames and still permits unknown native windows.
  Tooltip origin correction requires an exact native controller/source link,
  with rejection of other speech instances and unrelated hovered windows.
- Twelve synthetic `audit_phase3b.py` fixtures accept healthy bounds and reject
  missing/newer runs, missing samples, invalid or out-of-screen regions, disabled
  fitting, invalid scale and operational failures. Actor-attached room titles
  and native fullscreen regions keep their documented policies.
- `verify_hooks.py` validates the existing 19 direct callsites, bitmap/input
  patch spans and return sites, viewport fields, connected layout, popup
  constructors/registration and player-gauge live placement evidence.
  No additional PRM callsite is patched for fitting or the settings panel.

The native world-ray, cursor, map/minimap and capture-tree paths retain their
existing implementations. Assembly thunks, export definitions and the build
script are unchanged. `ui_settings.h` is now a required source file for rebuilding.

The moving HP/SP bar is the exact UIPlayerGage window previously excluded by
the class-name gate. Its live bitmap center now avoids stale geometry groups.
The original character-name center policy is retained; the reported name/bar
overlap needs visual confirmation with the corrected bar. This build also
admits the exact transient explanation and character-info popup classes so
their first bitmap draw has ownership without a grouping warm-up frame.

## Runtime evidence and pending check

The saved accepted Phase 3A F8 audit passes: 22280 hit queries, 3356 selected-owner
scopes, 5416 competing candidates rejected, with Basic Info, Menu, minimap, chat,
quickslot and shortcut input regions. Normal unsupported/unowned draw counts are
informational. This supports the user's acceptance of the preceding click fix.

Phase 3B has not yet been exercised in-game. Restart, press F2, and try scale
changes with Keep on screen enabled. Place windows at the edges with F5 scaling
off, enable it, then check bounds, clicks and dragging. Include the connected
Basic Info/menu block. Close the panel with F2/Esc and confirm game input returns.
Hover descriptions at displayed controls and at their old unscaled positions,
switch controls and return, then walk and check the name/HP/SP alignment.
Press F8 after the test. The log auditor reports sampled bounds; host tests and
native API checks do not establish actual Wine panel appearance or every game
state. The working Phase 3A DLL/configuration is backed up before installation.
