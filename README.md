# PRM UI FIX — Return to Morroc UI Scaling

A 32-bit WinMM proxy that enlarges Return to Morroc's interface while keeping
window contents, mouse interaction and character movement aligned.

The current build is **Phase 2Z**. It includes complete-window scaling, topmost
window input, dragging, attached NPC descriptions, player chat-room titles,
character hover names, fullscreen map region previews and the compact minimap.
The game executable is left unchanged on disk.

## Compatibility

The native hooks target the **2020-09-02 PRM.exe client** used during development.
Other client builds need their hook addresses and object layouts verified.
The tested executable has SHA256:

```text
5b3fbd6b63d0e409dd0dbea0bcb389bab61d8e37a36855fe925a0a2310ea4d9b
```

Manual testing used Wine/Lutris at 3440×1440, initially at 133% UI scale and
then at 200%. The supplied INI retains the latest 200% configuration.
See [validation](VALIDATION.md) for the checks and their coverage.

## Install

1. Close the game and back up any existing `winmm.dll` and UI FIX configuration.
2. Copy this repository's `winmm.dll` and `prm-ui-fix.ini` beside `PRM.exe`.
3. Set `UI.ScreenWidth` and `UI.ScreenHeight` in the INI to the game's render
   resolution. Choose `UI.ScalePercent` between **100 and 200**.
4. For Wine/Lutris, set the environment variable
   `WINEDLLOVERRIDES=winmm=n,b`. Preserve any other overrides already configured.
5. Start the game. The proxy writes `prm-ui-fix.log` beside the DLL.

Keep the matching INI with this build. Configuration is read at startup, so
restart after changing resolution or settings. To uninstall, remove this
proxy and restore the files you backed up.

## Configuration

| Setting | Supplied value | Purpose |
| --- | --- | --- |
| `UI.ScalePercent` | `200` | UI enlargement, from 100% to 200% |
| `UI.ScreenWidth` / `UI.ScreenHeight` | `3440` / `1440` | Game render resolution used for UI anchors |
| `UI.SharpFilter` | `0` | Native smoothing; use `1` for point sampling |
| `Font.AddSize` | `0` | Preserve native font metrics and layout |
| `OwnerBitmap.Enabled` | `1` | Complete-window ownership and scaling |
| `WorldInput.Enabled` | `1` | Separate correction for terrain input |

UI anchors use the configured resolution; changing the game resolution while
running does not refresh them automatically. World input separately uses the
live viewport/client dimensions. Large fullscreen UI remains native size with
`UI.ScaleGlobal=0`. UI enlargement does not add automatic window layout or reflow.

The renderer enlarges existing cached bitmaps. Native smoothing generally looks
better at fractional scales; point sampling can make pixels sharper but uneven.
Larger replacement artwork or fonts do not automatically produce higher-DPI UI:
loading, bitmap resolution and logical layout would also need to support them.

## Shortcuts

| Key | Action |
| --- | --- |
| F3 | Switch native smoothing / crisp point sampling |
| F4 | Capture a trace, when enabled in the INI |
| F5 | Toggle UI scaling |
| F6 | Toggle UI mouse correction |
| F7 | Dump fallback UI groups |
| F8 | Dump ownership, input, minimap and renderer diagnostics |
| F9 | Toggle world input correction |

F11 and F12 remain available to the game. Runtime toggles reset on restart.

## Build

Building requires Bash, Clang, LLVM's `lld-link` and the `file` utility on Linux. The DLL is
freestanding and needs no Windows SDK or C runtime libraries.

```sh
./build.sh
```

The script writes `winmm.dll` in the repository root. `CLANG` and `LLD` can select
alternative executable paths. The proxy exports 185 WinMM names and loads the
real system WinMM dynamically.

## Verify and test

Python 3 and Clang are required. The host tests additionally need 32-bit Linux
execution support, 32-bit C headers/libraries, LLVM `ld.lld`, and Clang's
AddressSanitizer/UndefinedBehaviorSanitizer runtimes for the tested architectures.

Validate the native hooks against your own game executable:

```sh
python3 verify_hooks.py /path/to/PRM.exe
```

Run the host fixtures from the repository root:

```sh
for test in test_*.py; do
    python3 "$test" || exit 1
done
```

The fixtures extract production C functions and exercise ownership, input,
capture, minimap/map rendering, filtering, registry lifetime and assembly
argument forwarding. They do not launch the game.

For a runtime report, press F8 in-game and inspect the generated log:

```sh
python3 audit_phase2z.py /path/to/prm-ui-fix.log
```

The auditor reports missing samples as REVIEW. A successful diagnostic audit
still needs visual confirmation of layout and interaction. Without explicit
paths, the verifier and auditor use `~/Games/Refuge/` as a development default.

[Implementation notes](docs/IMPLEMENTATION.md) describe the native drawing paths.
[Validation](VALIDATION.md) records the tested build's identity and evidence.
