# Phase 3E validation

This build addresses the latest reports: a tooltip briefly changing appearance
on window reentry, hotbar slots highlighting at their old unscaled position,
and the chat's transparent background separating after resizing. In-game
confirmation of these changes is pending. The accepted F2 settings panel,
world input, buff attachment, health gauge and character-name behavior remain
covered by the existing regression checks.

## Artifact identity

`winmm.dll` is 210944 bytes, PE32/i386, with exactly 185 WinMM exports and no
static imports, IAT or delay imports. SHA256:

```
ed850ee31bf18f1ab07c214553270babc9f4f9ab28662a4c3790039c3d4aeeb1
```

The original PRM.exe remains unchanged, SHA256
`5b3fbd6b63d0e409dd0dbea0bcb389bab61d8e37a36855fe925a0a2310ea4d9b`.
The supplied INI remains 150%; installation replaces only the DLL and preserves
the user's live INI, currently 200%, native smoothing and KeepOnScreen enabled.
The accepted `ui_settings.h` is unchanged. `SHA256SUMS` covers the build inputs
and DLL. The work is local on `fix/tooltip-entry-and-buff-placement`; published
main remains Phase 2Z.

## Evidence and changes

The Phase 3D log showed all 24 captured first-appearance popups at 200% with
`nativeSize=0`, only 29 owner records, and no queue expiry, mismatch or overflow.
Owner capacity therefore does not explain this reproduction. The ordinary
popup can remain registered for up to 100ms after its last native refresh;
its translation previously depended on whichever window the pointer currently
selected. Leaving that window could remove its source translation.

The nonempty factory's timeGetTime call at VA 6284A2 now captures the source
on every update, preserving the exact native clock return. The +20 timestamp
validates the binding but is not treated as a unique update revision. The
popup retains its last producer's transform through leave/reentry and unrelated
hover changes. Actual factory updates replace or clear that binding. Actor
speech and the separate character-info factory retain their own rules.

The hotbar polls mouse globals from its virtual +40 callback, outside the two
hooked hit queries. The shared manager dispatch at VA 607F49 now supplies an
outside point to competing known roots for that callback. The selected root
receives its already inverse-mapped pair. Native callbacks and mouse restoration
are preserved, with no class-name gate. F8 reports update calls and filtering.

The user's chat F8 snapshot showed native `(0,983)`, size `600x96`, anchor
`(0,720)`, displayed at `(0,1246)..(1200,1438)`. Its unowned inner background
used anchor `(0,1440)` and appeared at `(8,528)..(1192,718)`. The native +A0
background callback submits multiple rectangles outside the existing single-box
wrapper. Scoping the manager's shared +A0 dispatch at VA 60BA14 gives those
rectangles the same owner transform as the cached bitmap, including on resize.

## Verification

All 20 host harnesses passed. They exercise extracted production functions with fake native
objects and Windows services. They do not launch the game.

- Tooltip lifetime: source retention after leaving, unrelated hover, same-tick
  refresh replacement, invalid refresh clearing, popup construction after the
  clock call, clock mismatch, actor speech exclusion, and disabled/capture gates.
- Window hover: actual i386 thiscall forwarding, scaled hit and former-location
  miss, overlapping arbitrary roots, identity/freshness checks, native-size and
  disabled/capture forwarding, and mouse restoration after nested callbacks.
- Chat background: the observed 3440×1440/200% geometry, row/frame/bitmap
  transform identity, delayed queue consumption across 250→96→250 height
  changes, another class using +A0, and unknown-owner scope isolation.
- Existing ownership, bounds, connected panels, drag/capture, topmost input,
  map/minimap, cursor/world input, filtering, owner lifetime, presentation,
  settings and buff regressions.
- Actual assembly thunks execute on i386, checking argument forwarding,
  return values, stack/register preservation, list advancement and continuations.
- Native verification passes 21 direct calls, 3 bitmap/background spans,
  3 input/refresh spans, 2 offscreen returns, the central mouse return, source
  constants and layout evidence against the original PRM.exe.
- The Phase 3E auditor is checked with synthetic current/old runs, missing
  snapshots, invalid bounds/counters and owner admission failures.

Logs and native evidence are retained under `evidence/phase3e-work/`; the
matching source and build are archived under `releases/phase3e/`.

## Next in-game check

Restart to load Phase 3E. Repeatedly leave and reenter the inventory while
hovering an item; hover the hotbar's former unscaled location and its displayed
slots; resize and move chat several times. Press F8 if an issue persists.
Wait for the user's feedback after handing over this build; do not poll for
manual-test completion.
