# PRM UI FIX implementation notes

Version 1.0. These notes describe the native client paths and the implemented
ownership rules in the refreshed release. For installation and settings, see
[README](../README.md) and [validation](../VALIDATION.md). The release binary
uses the same behavioral code as the tested build; only version labels changed
for the release rebuild.

The supported installation places `winmm.dll` and `prm-ui-fix.ini` beside
`PRM.exe`. Close the game before replacing either file and restart it after
configuration changes. Wine/Lutris users should set
`WINEDLLOVERRIDES=winmm=n,b`, preserving other overrides. Windows and dgVoodoo
with the DirectX 11 renderer are untested.

## Startup resolution

`UI.AutoDetectResolution=1` reads `savedata\OptionInfo.lua` beside the installed
DLL at startup. Only literal `OptionInfoList["WIDTH"]` and
`OptionInfoList["HEIGHT"]` assignments supply dimensions; `OLD_WIDTH` and
`OLD_HEIGHT` are ignored. The file is treated as data and no Lua is executed.
Both dimensions must be valid before either replaces the INI fallback: width
640..16384, height 480..16384. Missing, unreadable, malformed or oversized files
leave `UI.ScreenWidth` and `UI.ScreenHeight` in effect. Setting automatic
detection to zero selects those manual dimensions directly.
Manual dimensions are bounded to the same range before use.

The loader resolves `ReadFile` through the existing dynamic API mechanism,
reads at most 64 KiB plus an overflow probe byte, and closes the handle before
parsing. The large buffer has static storage; the startup path introduces no
CRT dependency or large stack allocation. A truncated DLL path is rejected.
The effective dimensions and their source are logged before hooks are armed.
Detection runs once per process, so changing the game's saved resolution
requires restarting the game. Overlay saves do not write these settings.
The user-confirmed Linux/Wine startup check at 200% selected 3440x1440 with
`AutoDetectResolution=1` and `SharpFilter=0`.

## Screen bounds and live settings

A window uses `anchor + (native_point - anchor) * fit_scale + offset`.
`fit_scale` starts at the configured percentage and is reduced uniformly if
the whole bitmap is larger than the configured screen. `owner_fit_rect` then
corrects any left/top/right/bottom overflow. Each ordinary owner's additive
offset persists independently from its base anchor and native position.
Recomputing the offset from zero would trap a window at the edge while its
native coordinates moved through the hidden overflow; retaining the correction
lets subsequent drag deltas move it inward immediately.

The transform is copied through bitmap scopes, queued vertex records and input
regions. All tiles/overlays share it; deferred vertices keep their recorded scale
even if the global setting changes. Inverse input subtracts the same offset and
divides by the same scale. Capture freezes the starting transform so boundary
corrections cannot feed back into the game's drag delta. Input publication admits
fitted bitmap bounds up to the already validated 8192-pixel source limit, including
native origins outside the screen. Native positions are never rewritten.

Basic Info and Menu are independent manager roots with an explicit native layout
relationship: 5FF205 selects Menu ID 0x133; 5FF237..248 passes Basic's absolute
position and height to Menu's virtual position method ACF730, which subtracts
four pixels vertically. IDs are stored at object+2C (606ADF). The fitting helper
requires both active, enabled, unparented objects, their exact classes and live
vtable identities. It fits their union using Basic's anchor and shares the
result across both roots for the frame. Unknown/unrelated windows are not joined.
Real child controls already belong to their parent's whole-window bitmap.

Cursor-following descriptions receive a fresh edge correction, so an old offset
does not detach them from the pointer. World-attached descriptions, room titles
and hover names retain their accepted actor attachment rules. Native-size
fullscreen UI remains under its previous policy rather than the movable-window
fit policy. The geometry fallback is unchanged.

The configured overlay shortcut (Shift+P by default) toggles a settings panel drawn into the game frame. The existing game HWND
receives a subclass that queues keyboard commands. The present thread owns the
menu state and applies changes after native capture ends. No window is created
and no focus/activation or display-mode API is called. Enter applies; S saves
and closes, writing only ScalePercent, Enabled, SharpFilter and KeepOnScreen.

Keybinds are loaded from the INI at startup. The game window procedure matches
exact modifier chords and queues each configured action once per press. Blank
bindings pass through to the game. Shortcut repeats and their generated text
are consumed, and focus loss clears held-key tracking. Panel navigation remains
arrows, Enter, S and Esc; Alt+F4 preserves the native close command.

DirectDraw surface GetDC/ReleaseDC bracket GDI drawing after the native frame
has been composed and before presentation. The DC state and selected objects
are restored; temporary GDI objects and COM references are released. API or
drawing failure closes the menu so an invisible panel cannot retain input.
The DLL keeps dynamic API resolution and empty import directories. Host tests
exercise the 32-bit stdcall ABI and resource cleanup; they do not establish
actual Wine appearance or display-driver support.

DumpDiagnostics adds live UISettings and each input owner's fit percentage, correction offset
and displayed rectangle. The bounds auditor checks the newest run/sample and
distinguishes diagnostic coverage from the user's interaction result.

## Framed-window admission

Ordinary dialogs also derive from `UIFrameWnd` without necessarily naming their
leaf class `Wnd` or `Window`. `UIMessageBox`, `UIMessageBoxAutoreturn`,
`UIAgitMessageBox` and `UINoticeMessageBox_LockSellItem` all have native
`UIFrameWnd -> UIWindow -> UIRPData` ancestry with PMD `(0,-1,0)`.
The corresponding primary RTTI locators are DB31D4, DB3228, DA9AA0 and DAA088.

State admission now checks a bounded native RTTI base array when the existing
semantic classification has no rule. Both UIFrameWnd and UIWindow must be
nonvirtual bases at the object's current address. This admits generic framed
windows, including confirmation dialogs, into the existing bitmap, input and
capture paths. It does not depend on a list of dialog leaf names. Names and all
RTTI metadata are checked against the executable image bounds before reading.

UIWindow alone is too broad for this fallback: the native hierarchy also includes
raw bitmap controls, world-attached gauges and balloons. Those retain their
existing classification and attachment policies. The native hierarchy audit
identifies eight newly admitted framed classes, including the four confirmation
families, UINormalMB, CMergeItemWnd, CUICollectionSystemWnd and UIGuild_Storage_Log.

## Fullscreen map and hover-name draw order

The manager registers UIRoMapWnd in list +174 and stores it at manager +3C4.
Its scene-sized image is drawn through the existing map call at 60BA38. A
transient character-name window registered later can otherwise be drawn after
the map, leaving the name visible over that image.

The map renderer records an occlusion marker only after its original draw runs.
The marker is valid for the current frame and render thread, identifies the
native map object/vtable, and requires visible fullscreen bounds. Later
UINameBalloonText and UIVerticalNameBalloonText bitmap and background draws are
suppressed while that map identity and geometry remain valid. A name drawn
before the map retains normal rendering and is covered by the map itself.
The marker expires at the next presentation; hiding/replacing the map revokes
it immediately. Other windows and actor-attached UI retain their existing rules.

This is a rendering correction. The accepted raw-pointer world ray, movement
input and native map-region interaction remain unchanged.

## Native hit ownership

The incident log at 200% records `UIBasicInfoWnd` at native (80,902), size
220x134, anchor (0,1440), and `UINewChatWnd` at (0,827), size 600x250, anchor
(0,720). Basic Info displays at (160,364)..(600,632); chat displays below it,
at (0,934)..(1200,1434). A Basic Info click at (300,450) converts to (150,945),
which also lies in chat's original rectangle.

Both classes use native hit method B217C0 through vtable slot +B8. That method
checks an enabled rectangle, descends through children, then returns a child or
root. `UIMenuIconWnd` uses its own ACF590 override. UIWindowMgr's 5FA1A0 selects
from native list +174, then updates hover IDs and invokes enter/leave callbacks.
Discarding the visually chosen owner before that scan allows another root to
steal the converted point.

Two narrow calls (5F862C event routing and 609FCE uncaptured input) now scope the
native query. The root candidate call at 5FA1C2 changes from the six-byte virtual
call to a relative wrapper call plus NOP. The wrapper calls each admitted root's
original +B8 method. Identified, current competing roots are skipped only for a
matching chosen input sample; unknown roots retain native behavior. All native
child recursion, return values, hover callbacks and later modal restrictions
remain in the original manager. The +194 capture branch remains untouched.
Selection and rejection use object identity and copied regions, with no window
class-name conditions. The same path handles every tracked interactive root,
including roots whose original virtual hit method differs from B217C0.

ScreenToClient at return 895BE1 refreshes the native point on WM_MOUSEMOVE;
button events can reuse that point for many frames. A copied raw/mapped sample,
owner identity and thread therefore persist until the next central mouse sample.
Each query requires matching thread and coordinates, a fresh copied owner
region, the same current visual winner and transform, and the owner's original
vtable. A four-byte identity check is the only added live owner read; bounds and
ownership use copied snapshots. Missing/stale/reused records, disabled scaling,
capture and unrelated coordinates forward normally. Samples from other
ScreenToClient callers do not overwrite this native mouse record.

A central sample outside every displayed input region now remains a valid
miss, with no selected object. Revalidation confirms the same visual miss and
the candidate wrapper rejects all currently identified roots. This prevents
hover callbacks at their old unscaled rectangles. Unknown roots still use
their original methods. A previously selected owner disappearing does not
become a miss implicitly; that stale selection follows the existing bypass.

The new hooks validate original call targets and bytes, flush the instruction
cache, and keep filtering disabled after partial installation. No shared method
entry, game window position or vtable is rewritten. DumpDiagnostics adds `OwnerHit` queries,
scoped queries, rejected competing candidates and unmatched query counts.

## Transient explanations and player gauge

The RTTI suffix gate missed `UITransBalloonText`, `UICharInfoBalloonText` and
`UIPlayerGage`, although they are actual manager-backed UIWindows. They now use
the existing final bitmap ownership boundary immediately, with passive input.

Generic control explanations call 628430. For example, the button method at
4E9060 converts local (0,-20) through B1E150 and calls the factory at 4E92A1.
The factory constructs UITransBalloonText (4DCCF0, vtable D31CF0), registers it
at 628500 and sets the native position at 6285AE. UICharInfoBalloonText uses
59F8D0, vtable D3CD8C and registration at 59F9AB. Their cached pixels remain
native until the final manager bitmap draw. The tooltip origin is translated
through its source owner's scale/offset, then its pixels are enlarged once.
The ordinary tooltip must be the exact controller E78D8C's +1C object. Phase
3E observes the nonempty factory's clock call at 6284A2, preserving its native
timeGetTime result and binding the copied source on every update. The +20
timestamp is checked for invalidation; it is not treated as a unique revision.
The expiry routine at 6286A0 can leave the popup visible for 100ms after the
pointer leaves. During that interval its source remains the last factory's
source, even when the pointer moves over another window. A new factory update
replaces that binding, including two updates in the same clock tick.
Phase 3F also captures the original x/y arguments from factory EBP+0C/+10.
Native 628560..5AE clamps those arguments into [-3, viewport-size+3] before
SetPos. That clamp can detach a tooltip from a window whose native coordinates
are offscreen while its fitted display is visible. The bitmap origin now moves
to `sourceTransform(requestedOrigin)` using an offset relative to its actual
clamped cache origin. The existing popup fit then keeps the enlarged result on
screen. Native position writes, text layout, cache contents, and clock return
remain unchanged. The clock bridge forwards three stdcall arguments (12 bytes).
The character-info popup still matches its selected source root's +19C8 field.
The inactive character-info position (-400,-400) remains hidden.

The translucent background is a separate manager submission. UITransBalloonText's
virtual +18 method (4E42A0) returns its background rectangle and true. The manager
then calls cdecl 492660 at 60B9E8 before drawing the text bitmap at 60BAA3/60BAD4.
Previously that background reached the geometry fallback with no owner. A narrow
call wrapper now carries the manager's EDI owner into the same whole-window
bitmap preparation used by the cached text. The existing rectangle queue records
its transform, and the enclosing scope is restored. This applies to every admitted
window using that background path, without a buff-name or size heuristic.
The cdecl bridge retains the caller's five original arguments and its cleanup.

The manager's other background protocol calls virtual +9C followed by +A0.
UINewChatWnd uses that second path: +A0 (579EC0) emits multiple rectangles
through 492660. Phase 3E scopes the shared +A0 dispatch at 60BA14 using the
window's actual vtable target. Those rectangles now receive the same owner as
its cached bitmap, including while the native chat dimensions change. The DumpDiagnostics
reproduction showed the unowned inner chat background using anchor (0,1440)
while the chat itself retained (0,720), producing a 720px separation at 200%.

Window updates at 607F49 call every active root's virtual +40. UIShortCutWnd's
592FD0 reads mouse globals E83374/E83378 there, bypassing the hit-query hooks.
Phase 3E wraps this shared dispatch and checks the copied visible owner. A
known root under another window or at a displayed miss receives an outside
point for that callback so its own native code clears hover. The selected root
receives the already inverse-mapped pair. Both globals are restored before
the manager advances to another window. Capture, disabled input, stale samples
and unknown roots retain native forwarding. This policy has no class-name test.

UITransBalloonText also carries actor speech at 719D11..9E14. Those other
instances receive a live bottom-center attachment and no source-window
translation or screen fitting. Hovering an unrelated control therefore cannot
pull world speech away from its actor. All these text popups remain passive.

UIPlayerGage (constructor 4F8320, vtable D3418C, renderer 512F90) is distinct
from the UIBarGraphPlayer controls inside normal HUD windows. The world UI
object stores it at +2C8 and registers it through 5F4DD0. Per-frame placement
at 742788..280B reads the actor projection +AC/+B0, centers the 60-pixel bar
at projection X and applies a signed vertical offset. The final bitmap now
scales around its current integer center, without screen fitting or input
ownership. No actor projection or name-placement code is patched. The user confirmed both the health bar and name placement in-game.

## Compact minimap

The game draws the map image and its direction/position markers from a scene
routine before UIWindowMgr draws the coordinate text and zoom controls. Those
direct graphics previously escaped ownership, leaving the map small while its
controls enlarged elsewhere.

The scene draw now borrows the exact `UIMinimapZoomWnd` owner stored at
UIWindowMgr+1A8. Its map image, textured markers, direction marker and cached
controls share the same complete-window transform. Native zoom still changes
the map contents; UI scaling enlarges the whole display. The existing copied
input region and child capture map the enlarged controls back to their native
coordinates. The original scene object and all queued source vertices are
preserved. DumpDiagnostics records `Minimap draws` and the minimap owner region.

The fix uses the narrow scene call at VA 74024D and the image/direction queues
at 62835F/7325C4. It adds no global drawing hook or original-executable edit.
The expanded map and fullscreen world map retain their existing paths.

## Character hover names

`UINameBalloonText` and `UIVerticalNameBalloonText` were excluded by the old
Wnd/Window class-name filter. Their unowned graphics could inherit unrelated
fallback group anchors. Both exact classes now use the complete-window bitmap
path. Every tile shares the live name bitmap's center, refreshed as the native
game moves or resizes it, and frozen into each queued draw.

Native placement at VA 73D3D0 supports several layout modes and viewport clamps.
Keeping the bitmap center fixed preserves that placement without reproducing
actor projection or changing its layout. These labels have no pointer tail.
Their text, outlines, and emblems enlarge together. Names remain passive:
no mouse regions or capture-tree aliases are published for them. DumpDiagnostics includes
name class, position, size, anchor, and inputOrder=0 in its visual-only records.

## NPC service plaques

The game projects each NPC position and moves a `CSignBoardWnd` to that point.
This real UIWindow subclass was excluded before Phase 2W. It
therefore reached the geometry fallback and could be scaled around unrelated
screen edges. Phase 2W established native placement through whole-window bitmap
ownership. The user's follow-up requests enlargement too. Phase 2X scales every
tile and overlay around the plaque's live center, recovering the integer
half-width/half-height offset used by native placement at VA B6C430. That center
is updated each frame as the NPC projection moves, and copied into each queued
draw. Passive plaques do not publish mouse regions or enter fallback grouping.

This is an exact class rule, not a rectangle-size heuristic. Ordinary windows
with the same dimensions continue to scale. No new executable hook is needed.

## Player chat-room titles

The bubble showing a message and occupancy such as `(1/20)` is
`UIChatRoomTitle`. Its exact RTTI name lacks the suffix required by the old
filter, so it escaped ownership and could move toward an unrelated screen edge.
It now uses the existing complete-window bitmap path and remains interactive.
The title, child text, frame, and bottom pointer share a live bottom-center
anchor. Both drawing and copied mouse regions use that anchor as the player or
camera moves. Nearby ordinary windows retain their own transforms.

Native evidence: vtable D32AE0, creation at 719A13 (140x34), manager registration
at 719A42, position updates at 7130DB..713121, and the centered bottom pointer
paint at 4E6E34..4E6E5B. The title event formats `%s (%d/%d)` using the string at
D334AC. This identifies the reported room-title bubble. Character hover names have
their separate Phase 2Y rule above; spoken-message classes remain separate.

## Child capture boundaries

The old traversal reported overflow when a list ended at exactly 512 children;
it also silently stopped with queued work after 4096 visited objects. Those
boundary conditions now distinguish complete traversal from truncated work,
without increasing either limit. Recently drawn root objects must still have
their saved vtable before their children are read, matching input publication's
existing identity check. This rejects unreadable or changed root objects.

DumpDiagnostics distinguishes `capacityLimits`, `walkLimits`, rejected `staleRoots`, and the
peak number of copied links. Up to four limit events include the exact root,
object, list node, and frame. The first Phase 2W test had one undifferentiated
overflow; the next run had zero. These fixes are covered by reproductions, but
neither old log proves what caused that one event.

## Map region previews

`UIRoMapWnd` uses a separate manager call to draw region shading, preview
images, links, paths, and an animated marker. Those direct screen submissions
previously escaped the window's bitmap scope. Phase 2W captures that call and
six additional native queue callsites, so these graphics inherit the complete
map's transform. Region text already painted into the map bitmap follows the
same ownership.

The map is created with the renderer's full-screen dimensions. With the existing
`UI.ScaleGlobal=0`, the map and its region previews remain native size. The map
also publishes an identity input region at its native draw order, so HUD windows
behind it cannot apply their inverse scaling to map hover input. A newer window
above the map can still use its own input transform.

## Sharper UI

The native renderer uses linear filtering for its UI textures. The UI's text,
icons, and borders are already pixels in cached bitmaps before the configured UI scale
is applied. Crisp mode uses point sampling for each draw the mod actually
scales, then immediately restores the device's previous min/mag filter states.
Unscaled draws keep their original filtering. Device state is queried for each
scope, so native state-block changes are respected.

Crisp mode removes interpolation softness. It cannot add detail missing from
source bitmaps, and pixel widths can look uneven at a noninteger scale such as
133%. ToggleFiltering switches between crisp and the game's original filtering without
changing layout, font metrics, UI scale, or mouse mapping. The user's Phase 2W
comparison favored native smoothing, which now starts enabled
(`UI.SharpFilter=0`). Set it to 1 to start in crisp mode. `Font.AddSize=0`
remains unchanged; simply enlarging the font could overflow native controls.

Higher-resolution replacement artwork and fonts do not automatically make this
path render at higher resolution. Text and artwork are composed into native-size
window bitmaps before this mod enlarges them. Improved same-size assets may look
better, but larger asset dimensions need compatible loading and layout; this
mod does not implement a separate logical size for replacement textures. Font
hooks retain the game's requested font size with `Font.AddSize=0`, so replacing
an outline font still rasterizes it at that size. True higher-resolution UI
would need denser backing bitmaps and font rendering while preserving logical
layout and input coordinates.

The UI texture coordinates already include the game's half-texel offset. This
phase preserves that alignment and makes no geometry adjustment for sharpness.
