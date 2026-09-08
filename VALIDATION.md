# Phase 3C validation

The user confirmed Phase 3B's health-bar and character-name alignment. They also
reported that buff explanation text was outside its box, and that F2 switched
to the desktop settings window and left the game stuck after Apply/Save.
Phase 3C addresses those two reports on `fix/in-game-settings-buff-tooltip`.
Public `main` remains Phase 2Z. The new focused in-game check is pending.

## Artifact identity

The DLL is 195072 bytes, PE32/i386, with exactly 185 WinMM exports and no
static imports, IAT or delay imports. All 15 host harnesses passed.

| Artifact | SHA256 |
| --- | --- |
| `winmm.dll` | `d81890b5c1ac6510afb627b47a5e95f4cd5693f965986a3363157cbc04fe3537` |
| `prm-ui-fix.ini` | `8f1de12782d8a1579f97cece702bf3d361a262014918afbbe04ba7fa1e5a5c36` |

The target PRM.exe remains unchanged, with SHA256
`5b3fbd6b63d0e409dd0dbea0bcb389bab61d8e37a36855fe925a0a2310ea4d9b`.
The supplied INI uses 3440×1440, the user's requested 150%, native smoothing,
and unchanged font metrics, with KeepOnScreen enabled.

## Changes and evidence

The translucent tooltip background is drawn before its cached text bitmap.
UITransBalloonText's virtual +18 method at 4E42A0 returns a background rectangle
and true; the manager calls cdecl 492660 at 60B9E8. That rectangle previously
escaped bitmap ownership and used the geometry fallback while the text used its
window's transform. A narrow wrapper now carries the manager's EDI owner into
whole-window preparation for the rectangle. The existing rectangle queue freezes
the transform, just as it does for text tiles. The enclosing scope and native
arguments are preserved. This covers all admitted windows using that manager
background path, including buff explanations. Actor/name/gauge anchor policies
are unchanged.

F2 now draws settings into the game frame using DirectDraw GetDC/ReleaseDC and
GDI. A subclass on the existing game window queues keyboard commands; the
present thread owns the draft and commits changes after any drag ends. There
is no separate settings window, message thread, focus change, or display-mode
change. Enter applies; S saves and closes; F2/Esc closes. Save writes only the
four UI settings. Rendering failure closes the panel and releases input.

The initial incident snapshot had no apply/save completion and still specified
200%. A later capture, taken after detecting an INI change during packaging,
records both Apply and Save completing at 150%, with KeepOnScreen enabled.
The later file is preserved. The reported desktop switch and stuck presentation
support removing the external focus-taking panel; these captures do not establish
the exact Wine/DirectDraw focus-loss internals or current visual game state.

## Local verification

- The background fixture exercises actual scope preparation, bitmap ownership
  and vertex scaling with native-sized fake objects, including first draw,
  queued background/text agreement, nested scopes and unknown-owner forwarding.
- `test_thunks.py` executes the production assembly on i386: both bitmap
  continuations, the background's EDI owner, five cdecl arguments, return value,
  native caller cleanup and preserved registers.
- `test_settings.py` exercises the actual header and core Apply/Save functions
  with the i386 stdcall ABI, keyboard routing, deferred opening/commit during
  capture, settings persistence, DC cleanup and draw failures.
- `test_present.py` exercises Blt/BltFast/Flip target selection, original argument
  and return forwarding, drawing before presentation, reverse/offscreen copy
  exclusions and COM reference handling.
- Existing ownership, hit selection, captured-child input, bounds, connected
  Basic Info/Menu, cursor, world input, drag, filtering, map and minimap tests
  retain their coverage. The bounds fixture covers 125/133/150/175/200% and
  720/1080/1440-high screens.
- `verify_hooks.py` checks 20 direct callsites, two bitmap patch spans, one input
  patch span, offscreen and mouse return sites, plus native layout evidence.
  Only the new manager background call is added to the PRM patch set.

These host fixtures use fake Windows/COM services and do not launch the game.
The PE32/i386 DLL retains 185 WinMM exports and dynamic API loading. The export
definition, forwarder assembly and build script are unchanged.

## Pending in-game check

Fully exit the stuck game and restart to load Phase 3C. Check a buff explanation
at the displayed icon, then switch buffs and return. Open F2, adjust the scale
with Left/Right, apply with Enter, save and close with S, and reopen/close with
F2 or Esc. Confirm the game remains visible and movement/clicks resume. Press
F8 after the combined check. The new bounds auditor reads Phase 3C snapshots;
it cannot determine visual tooltip alignment or fullscreen focus behavior.
Previous DLLs and configurations are preserved in the project archives and
evidence folder; development backups and reports do not belong in the game
installation.
