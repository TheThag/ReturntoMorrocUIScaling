# Phase 2Z validation

The user reported manual testing complete before requesting publication. No new
defect was reported. This repository contains the exact source and DLL supplied
for that test; publishing did not change the implementation or the configuration.

## Artifact identity

| Artifact | SHA256 |
| --- | --- |
| `winmm.dll` | `1ce39b6eb3dcf494879455df53f25b32986edfbda2b2a817ffbefd71a6e9fc42` |
| Target `PRM.exe` | `5b3fbd6b63d0e409dd0dbea0bcb389bab61d8e37a36855fe925a0a2310ea4d9b` |
| `prm-ui-fix.ini` | `bea46a21132b93954950d0a433a217f10eb77265fb5287e1d5f791ce473966bb` |

The DLL is 169984 bytes, PE32/i386, with exactly 185 WinMM export names and empty
normal-import, IAT and delay-import directories. The target executable was not
modified on disk. The supplied configuration uses 3440×1440, 200% scaling,
native smoothing and unchanged font metrics.

## Local verification

Before the manual test, the freestanding build and native hook verifier passed:
17 direct callsites, two bitmap patch spans, two offscreen return sites, the
minimap manager reference, source RVAs and native viewport fields.

- `test_minimap.py`: 32-bit ASan/UBSan checks for native owner lookup with a
  distinct scene object, shared image/marker/control transform at 133% and
  200%, frozen queued transforms, source vertex preservation, scope/return
  restoration, invalid owners and disabled scaling.
- `test_drag.py`: minimap map/control coordinates and captured child aliases
  inverse-map correctly at 133% and 200%; outside points stay unchanged.
  Existing title, topmost overlap and drag checks also pass.
- `test_bitmap.py` and `test_capture.py`: existing tiled-window, ownership
  registry, live name/plaque/title anchors, passive input, bounded capture
  and stale-root ASan/UBSan cases pass.
- `test_map.py`: the 32-bit full-map wrapper/queue and native/scaled input
  policies pass.
- Synthetic `audit_phase2z.py` fixtures accept valid records and reject
  missing/invalid/stale records and failing counters.

Twenty-six protected production functions match the accepted preceding build,
including world/cursor handling, input transforms, full-map scope, manager
bitmap wrappers, final scaling, filtering and world-attached class rules.
Assembly thunks, export definition and build script are unchanged. The other
included harnesses cover those previously verified paths.

Before publication, a clean copy containing only the 25 repository files passed
all ten host harnesses and the freestanding build. Its rebuilt machine-code
section matches the tested DLL exactly; PE32/i386, all 185 exports and empty
import directories were reverified. The repository retains the original tested
DLL and its checksum. The native hook verifier also passed against PRM.exe.

## Runtime evidence and limits

Earlier user tests accepted ordinary UI interaction, dragging, world movement,
full-map region previews, NPC descriptions, chat-room titles and hover names.
The compact minimap was the final reported omission, addressed by Phase 2Z.
After the focused minimap test request, the user replied "its done" and asked
to publish the project.

The saved final log confirms Phase 2Z startup at 3440×1440/200%, all minimap and
bitmap hooks, real WinMM, Direct3D hooks and raw world input. Its recorded
heartbeat has six owner/manager regions, 428 owner mouse mappings, 54 overlap
candidates, zero queue overflow and zero invalid positions.

That run has **no F8 snapshot**. Detailed minimap owner records, scene counts
and bitmap F8 counters are therefore unobserved; the focused log auditor
returns REVIEW, not PASS. Absent counters must not be interpreted as zero.
Manual testing was performed by the user. Host fixtures and static inspection
do not independently prove visual correctness or cover every game state.

Raw logs, screenshots and historical development archives are retained locally.
