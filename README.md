# Return to Morroc UI Scaling — UI FIX

UI FIX enlarges the game interface while keeping clicks, dragging and tooltips
aligned with their windows. It includes screen fitting, corrected world input,
actor-attached labels, minimap support and an in-game settings overlay.

Release **1.0** was refreshed on 2026-09-08 with automatic resolution detection,
confirmation-dialog input fixes and fullscreen-map hover-name corrections.
The updated build was tested in-game on Linux/Wine. Windows remains untested.

## Download and install

Download **ReturntoMorrocUIScaling-1.0.zip** from the
[1.0 release](https://github.com/TheThag/ReturntoMorrocUIScaling/releases/tag/v1.0).
The repository contains source code; compiled DLLs are distributed as release assets.

1. Download the ZIP under **Assets**, then close the game. Preserve any existing
   `winmm.dll` and `prm-ui-fix.ini` outside the game folder.
2. For a new installation, extract `winmm.dll` and `prm-ui-fix.ini` beside
   `PRM.exe`. When updating UI FIX, replace its DLL and keep your INI to preserve
   your settings. Missing `AutoDetectResolution` defaults to enabled.
3. By default, UI FIX reads `savedata/OptionInfo.lua` beside `PRM.exe` once at
   startup and uses the literal `OptionInfoList["WIDTH"]` and
   `OptionInfoList["HEIGHT"]` values when they form a valid pair. If the file
   or either value is unavailable, it falls back to `ScreenWidth` and
   `ScreenHeight` under `[UI]`. Set `AutoDetectResolution=0` to always use those
   manual values. Choose `ScalePercent` between **100 and 200**.
4. For Wine/Lutris, set `WINEDLLOVERRIDES=winmm=n,b`, preserving other overrides.
5. Start the game normally. Press the configured overlay shortcut, **Shift+P**
   by default, to adjust the UI. New installations start at **150%**, with crisp
   filtering off and all other UI FIX shortcuts unassigned.

Only the DLL and INI need to be installed. The runtime creates `prm-ui-fix.log`.
To uninstall, remove the proxy and restore any files you preserved.
The ZIP includes [INSTALL.txt](INSTALL.txt) with installation, updating and
troubleshooting instructions. That guide and the checksums can stay outside the
game folder.

### Windows: possible dgVoodoo2 workaround

Windows and this workaround have **not been tested** for UI FIX. If the client
crashes on Windows, dgVoodoo2 with Direct3D 11 output may help; this is not a
confirmed requirement or crash fix.

1. Download the regular package from the
   [official dgVoodoo2 releases](https://github.com/dege-diosg/dgVoodoo2/releases).
2. Preserve existing graphics-wrapper files. Copy `DDraw.dll` and `D3DImm.dll`
   from its `MS/x86` folder beside `PRM.exe`, along with `dgVoodooCpl.exe` and
   `dgVoodoo.conf`. PRM is a 32-bit application even on 64-bit Windows. Keep the
   UI FIX `winmm.dll` in place.
3. Open `dgVoodooCpl.exe`, select the game folder as the configuration location,
   and set **General → Output API → Direct3D 11 (feature level 11.0)**. Leave
   **DirectX → Resolution** unforced, then apply and restart the game.

These wrapper setup options are described in the
[official dgVoodoo documentation](https://dege.freeweb.hu/dgVoodoo2/ReadmeGeneral/).
Keep wrapper DLLs local to the game folder. To undo the workaround, remove only
the dgVoodoo files you added and restore any previous wrapper files.

The supported client is the 2020-09-02 PRM executable, SHA256
`5b3fbd6b63d0e409dd0dbea0bcb389bab61d8e37a36855fe925a0a2310ea4d9b`.
Native hook locations are specific to this client. See [validation](VALIDATION.md)
for test coverage and known limitations.

## Settings

The overlay adjusts UI scale, scaling enabled, filtering and screen fitting.
Use the mouse or arrow keys, Enter to apply, S to save and close, and Esc to
close. Unsaved changes reset on restart. Saving updates those four UI settings
and preserves the rest of the INI.

| INI setting | Default | Purpose |
| --- | --- | --- |
| `UI.ScalePercent` | `150` | UI enlargement, 100%–200% |
| `UI.AutoDetectResolution` | `1` | Read `savedata/OptionInfo.lua` at startup; fall back to the manual resolution |
| `UI.ScreenWidth` / `UI.ScreenHeight` | `3440` / `1440` | Manual render-resolution fallback |
| `UI.KeepOnScreen` | `1` | Fit enlarged windows within the screen |
| `UI.SharpFilter` | `0` | Native smoothing; `1` selects point sampling |
| `Font.AddSize` | `0` | Preserve native font metrics and layout |
| `OwnerBitmap.Enabled` | `1` | Complete-window ownership and scaling |
| `WorldInput.Enabled` | `1` | Separate correction for terrain input |

Resolution and INI changes require a game restart. Autodetection reads the
relative `savedata/OptionInfo.lua` path once during startup and does not poll it
while the game runs. UI anchors use the selected resolution; world input uses the
live viewport/client dimensions. Fullscreen UI keeps its native size with
`UI.ScaleGlobal=0`. Enlargement does not reflow layouts.

The renderer enlarges existing cached bitmaps. Native smoothing generally looks
better at fractional scales; point sampling makes pixels more distinct. Higher
resolution artwork and fonts also need support from the client's bitmap loading
and logical layout to produce higher resolution UI.

## Configurable shortcuts

All UI FIX shortcuts are controlled by `[Keybinds]` in `prm-ui-fix.ini`.
Only the overlay has a default shortcut. A blank value disables an action.

```ini
[Keybinds]
Overlay=Shift+P
ToggleFiltering=
ToggleScaling=
ToggleMouseRemap=
DumpGroups=
DumpDiagnostics=
ToggleWorldInput=
CaptureTrace=
CaptureVirtualTrace=
```

Names are case-insensitive. Combine a key with `Ctrl`, `Shift`, `Alt` or `Win`
using `+`, for example `Ctrl+F8`. Letter and digit keys, F1–F24, arrow keys and
common named keys such as Enter, Esc, Space, Tab, Home, End, Insert, Delete,
PageUp and PageDown are supported. Modifiers must match exactly. Invalid values
disable the binding and are logged. Restart the game after editing keybinds.

`ToggleFiltering`, `ToggleScaling`, `ToggleMouseRemap` and `ToggleWorldInput`
switch their respective runtime options. `DumpGroups` and `DumpDiagnostics`
write troubleshooting information to the log. `CaptureTrace` additionally
requires `[Trace] Enabled=1`; `CaptureVirtualTrace` requires
`[VirtualTrace] Enabled=1`. These tracing options are disabled by default.

## Build and verify

Building requires Bash, Clang, LLVM's `lld-link` and the `file` utility on Linux.
The DLL is freestanding and needs no Windows SDK or C runtime libraries.

```sh
./build.sh
sha256sum -c SHA256SUMS
```

The build writes an ignored `winmm.dll` in the repository root. `CLANG` and `LLD`
can select alternative executable paths. The proxy exports 185 WinMM names and
loads the real system WinMM dynamically. Repository checksums cover source/build
inputs; release checksums cover the downloadable package.

Tests require Python 3, Clang, 32-bit Linux execution support, 32-bit C headers
and libraries, LLVM `ld.lld`, and Clang's ASan/UBSan runtimes.

```sh
python3 verify_hooks.py /path/to/PRM.exe
for test in test_*.py; do
    python3 "$test" || exit 1
done
```

The fixtures exercise production functions and assembly bridges without
launching the game. For a runtime report, assign `DumpDiagnostics` a shortcut,
restart, press it in-game, and inspect the latest snapshot:

```sh
python3 audit_phase3e.py /path/to/prm-ui-fix.log
```

Missing samples are reported as REVIEW. Without explicit paths, development
tools use `~/Games/Refuge/`. See [implementation notes](docs/IMPLEMENTATION.md)
for the native drawing and input paths.
