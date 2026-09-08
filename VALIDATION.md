# UI FIX 1.0 validation

The release retains the UI ownership and rendering implementation accepted in
manual testing through the Alt+V menu-tooltip correction. Version 1.0 adds
INI-controlled shortcuts, with Shift+P as the only default binding, and moves
the compiled DLL from source control into the release download.

## Automated verification

All 21 host test harnesses pass. They exercise the production ownership,
bitmap/background rendering, window bounds, connected windows, tooltip lifetime
and placement, buff descriptions, map/minimap rendering, drag/capture, input,
cursor, filtering, presentation, settings and owner registry paths.

The hotkey fixture checks missing and blank INI entries, alternate chords,
case-insensitive aliases, exact modifiers, invalid/truncated values, numeric
overflow, duplicate bindings and atomic per-action consumption. It also executes
the real runtime toggle consumers. The settings fixture checks message routing,
overlay activation, held keys, generated characters, focus changes, native
Alt+F4 behavior, apply/save, capture deferral and resource cleanup.

Native verification passes all 21 direct calls, 3 bitmap/background spans,
3 input/refresh spans, 2 offscreen returns, the central mouse return and layout
evidence. Assembly fixtures check argument forwarding, registers, return values,
stack cleanup and continuations. The runtime auditor accepts 1.0 and older 3E/3F
logs, isolates the newest run and rejects missing or invalid bounds samples.

The DLL is PE32/i386 with exactly 185 expected WinMM exports and no static
imports, IAT or delay imports. Source checksums are in `SHA256SUMS`; downloadable
package checksums are attached to the release. Host tests do not launch PRM or
prove every Wine/driver combination. The new keybind behavior has automated
coverage; it has not yet been manually tested in-game.

## Compatibility and manual coverage

The target PRM.exe is unchanged, SHA256
`5b3fbd6b63d0e409dd0dbea0bcb389bab61d8e37a36855fe925a0a2310ea4d9b`.
The user's in-game testing was on Wine/Lutris at 3440×1440, including 133% and
200% UI scale. The supplied INI defaults to 150%; other render resolutions must
be configured explicitly. Geometry tests include multiple resolutions and
133%, 150% and 200% scaling, but they are not a substitute for visual testing at
every resolution.

## Known issues reported during release preparation

- A character hover name can appear through the fullscreen map when the pointer
  is over the character's underlying world position.
- OK/Cancel buttons in native confirmation dialogs, such as skill-point
  confirmation and returning to login, may not respond with scaling enabled.
  Disabling scaling through the overlay allows those dialogs to be used.

These reports are recorded for the next fix. They are not represented as solved
by the 1.0 shortcut and packaging changes.
