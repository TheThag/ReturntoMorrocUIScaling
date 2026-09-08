# Phase 3A validation

Phase 3A addresses the reported unclickable Basic Info panel. It is a local test
build on `fix/basic-info-input`; public `main` retains the accepted Phase 2Z build.
The Phase 3A in-game check is pending. The user did not test whether F5 restored
clicks during the incident.

## Artifact identity

| Artifact | SHA256 |
| --- | --- |
| `winmm.dll` | `0448122ce7a4f0d5c2cf1104308a1ac6e052c7398e68bc9a215ce06826253c62` |
| Target `PRM.exe` | `5b3fbd6b63d0e409dd0dbea0bcb389bab61d8e37a36855fe925a0a2310ea4d9b` |
| `prm-ui-fix.ini` | `bea46a21132b93954950d0a433a217f10eb77265fb5287e1d5f791ce473966bb` |

The DLL is 174592 bytes, PE32/i386, with exactly 185 WinMM export names and empty
normal-import, IAT and delay-import directories. The target executable was not
modified on disk. The existing configuration remains 3440×1440, 200% scaling,
native smoothing and unchanged font metrics.

## Defect and scope

The saved Phase 2Z incident F8 snapshot records seven owner/manager regions.
Basic Info and its menu remain tracked; capture is released. Capture unknown,
queue overflow/expiry/mismatch, traversal limits and raw world/cursor failures
are zero. Minimap drawing and ownership are also recorded in this later log.

Basic Info displays at (160,364)..(600,632), separately from chat at
(0,934)..(1200,1434). Its visual point (300,450) inverse-maps to (150,945),
inside both original rectangles. Native manager traversal can then select chat
before Basic Info. Previously the selected visual owner was discarded after
coordinate conversion.

The new manager hit scope carries that owner through native candidate selection.
It applies to every current tracked input root by object/vtable identity, with
no Basic Info, chat or other class-name conditions. Each admitted root retains
its own original virtual hit method and child dispatch. Native capture, modal
restrictions, unknown roots and disabled-mode behavior remain native.
Stationary mouse samples are revalidated rather than expired after two frames;
the owner regions themselves must still be freshly published.

## Local verification

The freestanding build passes. `verify_hooks.py` validates 19 direct callsites,
two bitmap patch spans, one input patch span, two offscreen return sites, the
central mouse return, minimap manager reference, source RVAs and viewport fields.
Independent native/compiled-code review confirms the two query callsites, root
candidate span and thiscall argument/return convention, including stack cleanup.

- `test_drag.py` passes capture lifetime, child aliases, one-to-one physical
  drag deltas, overlap ordering, stationary snapshot freshness, disabled modes,
  fullscreen map occlusion, chat-title input and minimap controls at 133%/200%.
- `test_bitmap.py`, `test_capture.py`, `test_map.py`, `test_minimap.py` and
  `test_present.py` pass their existing ownership, registry lifetime, bounded
  capture, queued tile, map, minimap and present-order cases. The native object
  fixtures use 32-bit ASan/UBSan where required.
- `test_hit.py` reproduces the 200% native Basic Info/chat conflict and checks
  child results, distinct virtual methods, native-size windows, changed visual
  order, stale/reused identities, thread/coordinate gates, capture/disabled
  paths and nested scope restoration. One stationary sample remains valid
  across 32 fresh snapshots. Anonymous owners work in both traversal orders at
  125%, 133%, 150%, 175% and 200%, with no class labels in the input records.
  The production ScreenToClient wrapper is included: only its central caller
  publishes a selection, unrelated calls preserve it, and failed or unowned
  central samples clear it. Thiscall is preserved in the 32-bit ASan/UBSan
  fixture. Native Windows hook execution remains outside the host test.
- Synthetic `audit_phase3a.py` fixtures accept healthy owner/hit records and
  reject missing, stale or malformed samples and operational failures. Normal
  unowned/unsupported draw counts remain informational. Twelve independent
  follow-up fixtures also pass.

Twenty-eight protected production functions match accepted Phase 2Z exactly,
including world/cursor handling, capture mapping, final vertex scaling, bitmap
queues, map/minimap scopes, filtering, world-attached name rules and fallback
input. Assembly thunks, export definition and build script are unchanged.

## Runtime check still required

Restart with the existing settings. With chat visible, click Basic Info and its
menu icons, including after pausing the pointer. Drag the panel. Open and overlap
inventory, equipment and skill windows, and exercise their controls and dragging.
Press F8 afterward. `audit_phase3a.py` checks the newest run and snapshot for
active hit scopes and valid owner records. A diagnostic PASS does not establish
that the user interaction worked.

No Phase 3A game run or click outcome has been observed yet. Host fixtures and
native code inspection do not cover every game state. Native UI dispatch is
expected on one input thread; the scope is protected from torn copies and checks
thread identity, but simultaneous queries on different threads can lose the
selection override. Partial hook installation disables filtering and forwards
native behavior. These cases are not evidence of an observed in-game failure.

Raw incident logs and historical development archives remain local. The test
build is backed up and installed reversibly before the manual test request.
