# Crisp filtering investigation — 2026-09-21

Status: screenshots received; candidate crisp-sampling-r1 prepared for live validation.
The earlier scale-dependent half-texel hypothesis is not sufficient to explain
the reported 100% behavior.

## Verified source behavior

`ui_filter_begin` changes only stage-0 MAGFILTER (16) and MINFILTER (17) to POINT
(1), after `make_scaled_ui_vertices`. `ui_filter_end` restores both states.
The crisp flag does not participate in the vertex transform or input transform.
The production filter/draw harness passes DP/DIP, native forwarding, nested calls,
restoration and failure handling. It stubs the renderer and cannot prove GPU output.
Offscreen window composition retains native filtering; crisp is applied to the
final scaled draw. Thus already filtered content inside caches remains filtered.

## Native executable evidence

Inspected `/home/thag/Games/Refuge/PRM.exe` with llvm-objdump. Cached bitmap builder
VA 0x004AB3B0, submitted at 0x004AB5A1, constructs integer XY positions x,y through
x+w,y+h, with UV endpoints:

- u0 = 0.5 / texture_width
- u1 = (w + 0.5) / texture_width
- v0 = 0.5 / texture_height
- v1 = (h + 0.5) / texture_height

Constants VA 0x00E755FC and 0x00E75600 both decode to float 0.5. Instructions
0x004AB3FC–0x004AB454 compute these coordinates. Geometry stores begin at
0x004AB49F. The final native queue dispatcher passes the vertex pointer directly
to DrawPrimitive/DrawIndexedPrimitive; our scaler copies UVs and transforms XY.

At 1x these UVs place integer pixel centers on texel centers. Enlarging XY without
adjusting that phase is not equivalent to replicating native pixel cells. Under
integer pixel-center sampling, source texel coordinate is 0.5 + p/s; pixel-cell
aligned replication would use (p+0.5)/s. Their difference is (s-1)/2 screen pixels:
0.5 at 200%, 1 at 300%, 4.5 at 1000%. Point sampling makes the resulting texel
selection transitions abrupt, while linear sampling blends them. Fractional
scales and origins additionally produce uneven texel repetition. This is a
sampling phase difference, not proof that toggling crisp moves geometry by that
amount, and not a measurement of the user's screenshot.

A rational-arithmetic model is saved locally in
`evidence/crisp-investigation/sampling.txt`. For four native texels at 300%, the
current indices are 0,0,1,1,1,2,2,2,3,3,3,4 rather than 0,0,0,1,1,1,2,2,2,3,3,3.
Whether the final index reads padding, an adjacent atlas region, or a clamped
edge depends on the actual texture and address state. Exact tie outcomes can
also differ with floating-point interpolation.

## Next evidence and correction scope

Need the affected window/type, requested scale and crisp-off/on images at the
same position. Current INI has global 200%, hotbar 300%, buff icons 130%, minimap
1000%, with KeepOnScreen enabled; fitting can lower the effective scale.
The available recent log does not include a filter diagnostic snapshot.

A candidate correction would compensate sampling phase only for verified cached
bitmap quads, leaving owner placement and hit rectangles unchanged. Do not apply
a blanket half-pixel shift to every UI draw: sprite/atlas UVs, cooldown triangles,
solid backgrounds and existing native correction conventions need separate
validation. Compare tiled seams, alpha edges, clipping, fractional scales and
world/cursor exclusion before shipping anything.

Reference: Microsoft nearest-point sampling and texel/pixel mapping documentation
explains boundary sensitivity. These references describe D3D9; the native D3D7
builder above is the project-specific evidence, and the live Wine/wrapper path
still needs validation.
https://learn.microsoft.com/en-us/windows/win32/direct3d9/nearest-point-sampling
https://learn.microsoft.com/en-us/windows/win32/direct3d9/directly-mapping-texels-to-pixels

## Settings-path follow-up

Added a production-callback regression to `test_window_settings.py`: select each
registered type (and global), toggle only crisp twice, queue/poll/commit through
the real panel and core settings functions. Verify that global scale, enabled,
KeepOnScreen and the complete per-type preference registry remain unchanged.
The 32-bit ASan/UBSan harness passes. This rules out the ordinary crisp-only
settings application changing saved scales or offsets in the tested path; it
does not test the game's live window reconstruction or GPU rasterization.

The game process is running, but no configured desktop screenshot/control tool
is available, and xwininfo/xdotool are absent. No input was sent to the game.
An affected-window comparison is still needed to confirm the visible symptom.

Latest log recheck: log timestamp 2026-09-21 00:05:57 local now records
`Settings applied: scale=200 enabled=1 crisp=1 keepOnScreen=1`, followed by
skill-description and tooltip activity and a buff cooldown at effective 200%.
This confirms crisp was enabled in a live session, but supplies no pixel/UV
capture or identified defective element. The user-visible symptom remains
unconfirmed; investigation is blocked on an affected-window comparison.

## Screenshot evidence and crisp-sampling-r1

User supplied /tmp/codex-clipboard-3DG1T5.png (on) and
/tmp/codex-clipboard-hcdAAd.png (off), each 3440x1438. Equipment-window horizontal
rules and title shading show diagonal discontinuities in crisp mode; outer window
placement is unchanged. Native point sampling can magnify tiny interpolation
errors into a one-texel choice difference across triangles. Linear blending hides
the sharp discontinuity. This supports sampling precision as a cause, but actual
GPU-level confirmation and verification of the candidate remain pending.

The user reports the issue also at 100%. A production scaler test confirms an
identity transform returns a copied buffer, so pointer-based filter eligibility
still applies POINT at 100%. The scale-dependent phase mismatch described above
is zero at 100%; it is not an explanation for all reported artifacts.

Candidate: `ui_crisp_sampling.h` offsets UVs along each screen-axis gradient by
1/64 screen pixel. It does not move vertices, change input, or attempt a blanket
half-texel correction. All four owned draw entry paths invoke it on draw-local
copies after successful POINT setup. It admits only four-corner, axis-aligned,
uniform-depth/RHW, separable-UV rectangles with the known 0x1c4 layout. It bypasses
cooldown triangles, rotated/perspective geometry, invalid data and subpixel boxes.
Native unowned/offscreen draws and crisp-off paths retain their original data.

`test_crisp_sampling.py` models float32 two-triangle interpolation with native
uniform RHW, edge- and center-aligned UV conventions at 1x through 10x. The bias
removed 790641 synthetic disagreements with ideal point-sampling decisions.
This is not a real GPU rasterizer test. Fractional scales and flipped UVs retain
a constant subpixel bias, and non-UV fields remain byte-identical. Hook integration
tests exercise crisp off, failed filter setup, unmodified draws and original-buffer
preservation. Live comparison must check the original equipment/title seams,
100% and enlarged scales, tile edges, icons and cooldowns. A small bias can resolve
ties but cannot guarantee correction of unrelated atlas or offscreen-cache issues.

## Live acceptance

User reports the installed crisp-sampling-r1 build “seems perfect even at like
400%”. This confirms resolution of the reported visible seams in their live
comparison. All 34 automated scripts passed before installation; installed DLL
matches the archived candidate. No separate claim of exhaustive GPU coverage or
individual live checks for every window/scale is made.
