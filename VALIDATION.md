# Phase 3D validation

The user confirmed that Phase 3C's in-game settings menu works perfectly.
The remaining reports are an inventory tooltip flashing at native size on
window entry, and buff explanations appearing above their icons.
This build is on `fix/tooltip-entry-and-buff-placement`; the public main branch
remains Phase 2Z. The focused tooltip check is pending.

## Artifact identity

The DLL is 204800 bytes, PE32/i386, with exactly 185 WinMM exports and no
static imports, IAT or delay imports.

| Artifact | SHA256 |
| --- | --- |
| `winmm.dll` | `9108e45db455e1344acf8abaa7378473463f399aba28b09029fe1c61d435a9ca` |
| Supplied `prm-ui-fix.ini` | `8f1de12782d8a1579f97cece702bf3d361a262014918afbbe04ba7fa1e5a5c36` |

The original PRM.exe remains unchanged, SHA256
`5b3fbd6b63d0e409dd0dbea0bcb389bab61d8e37a36855fe925a0a2310ea4d9b`.
The supplied configuration remains 150%. Installation replaces only the DLL
and preserves the user's live INI, currently 200% with native smoothing and
KeepOnScreen enabled. The accepted `ui_settings.h` is unchanged.

## Buff placement

The native hover call at VA 741A30 invokes 75BF60 with the scene object and
mouse coordinates. That routine owns a separate UITransBalloonText at scene
+5E8; it does not use the ordinary tooltip controller's +1C popup. It computes
x = viewportWidth - 48 - column*45 - popupWidth, and y = 171 + row*35 before
screen clipping. The logged rectangle (3246,171,146,106) at width 3440 matches
that formula exactly.

A wrapper observes this exact producer and retains the scene and popup vtables.
Every use revalidates both identities and the scene's live +5E8 link. Only that
popup follows the buff HUD attachment; actor speech retains bottom-center
placement. The popup's native right/top attachment passes through the HUD
transform before its bitmap is enlarged. Background and text receive the same
transform. Oversized explanations still fit inside the screen. Fixed-origin
and centered anchor modes retain their configured origin.

## First-appearance ownership

The owner table previously stopped admitting objects permanently after 512
identities. A new tooltip could then use the geometry fallback, which can show
its first frame at native size before a group exists. The table now reclaims
its oldest stale, inactive record. A complete manager snapshot, recent drawing
and input activity, current scopes, capture and the selected hit owner protect
live records. An unreadable or incomplete manager walk blocks reclamation.
The manager is walked once per reclamation attempt, and no window positions
or input transforms are changed by reclamation.

This is a proven capacity defect, but the available runtime log does not prove
it caused the user's inventory flash. The inventory's native tooltip factory
already reaches the owned bitmap path. Bounded first-appearance log entries
now report popup identity, dimensions, selected source, scale, native-size
policy, and buff classification. They include reentry after a popup disappears.
F8 also reports owner-table size, reclaimed records and blocked admissions.
A visual result is needed to confirm whether the reported flash is resolved.

## Verification

All 17 host harnesses passed, including the new owner-lifetime and buff tests.
They exercise extracted production functions with fake native/Windows services;
they do not launch the game.

- Owner lifetime: actual 512-entry pressure, repeated transient tooltip churn,
  oldest activity selection, manager/current/capture/input protections,
  unreadable manager nodes, full-table blocking and vtable reuse under i386
  ASan/UBSan.
- Buff tooltip: exact scene/popup identity, native thiscall forwarding, queued
  background/text transforms at 150% and 200%, plus unrelated speech behavior.
- Existing bitmap, background, bounds, hit selection, capture, connected Basic
  Info/Menu, drag, cursor, world input, map, minimap, filtering, settings,
  presentation and assembly checks retain their coverage.
- `verify_hooks.py`: 21 direct callsites, two bitmap spans, one input span,
  offscreen/mouse returns and native layout evidence. The only added native
  patch is the buff hover call.
- PE artifact check: exact WinMM export set, architecture and absent imports.
- The Phase 3D auditor passes synthetic latest-run, missing-snapshot, old-run
  and blocked-admission checks; it cannot determine visual tooltip alignment.

## Pending in-game check

Restart the game to load Phase 3D. Hover an inventory item immediately after
entering the inventory, leave the entire window, and repeat. Check a buff
explanation beside its icon, then another buff and return. Press F8 afterward.
The first-appearance samples are automatic; no split-second capture is needed.
The user has already accepted F2, so this check focuses on the two tooltips.
Runtime files alone belong in the game folder. Archives and test evidence stay
in the project. Stop after handing over this build and await the user's result.
