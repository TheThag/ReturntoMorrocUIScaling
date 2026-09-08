# PRM UI FIX implementation notes

Phase 2Z. These notes describe the native client paths and the implemented
ownership rules. For installation and settings, see [README](../README.md).

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
preserved. F8 records `Minimap draws` and the minimap owner region.

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
no mouse regions or capture-tree aliases are published for them. F8 includes
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
it also silently stopped with pending work after 4096 visited objects. Those
boundary conditions now distinguish complete traversal from truncated work,
without increasing either limit. Recently drawn root objects must still have
their saved vtable before their children are read, matching input publication's
existing identity check. This rejects unreadable or changed root objects.

F8 distinguishes `capacityLimits`, `walkLimits`, rejected `staleRoots`, and the
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
133%. F3 switches between crisp and the game's original filtering without
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
