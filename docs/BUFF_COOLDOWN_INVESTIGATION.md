# Current test build: cooldown-owner-r2

User confirmed hotbar cooldown detachment persists after reverting the buff-only
experiment. The previous attribution of that hotbar issue to the experiment
was therefore not established.

The new implementation covers window builders at VA 58E6A0 and 59091F as well
as buff builder 66DB8D. Both window calls pass native window +1C/+20 coordinates.
Their original this pointers are saved in caller frame locals -768 and -774;
those stores are validated before installation. Adapters forward the actual
window to the C bridge. owner_bitmap_prepare provides the exact bitmap anchor,
scale and fit correction. No proximity matching or shared-flush owner guessing
is used. The buff path uses its existing scope independently.

Archive and validation notes: releases/cooldown-owner-r2/README.md.
Live attachment still needs user confirmation, including dragging and map changes.

---
Historical investigation (superseded where contradicted above):

# Status: experimental change reverted

User testing found that the experimental cooldown change moved hotbar cooldowns
and did not fix the intended buff cooldown. The producer hook and expanded
24-vertex ownership records have been removed. The hotbar position fix remains.
The static interpretation below did not establish sufficient live provenance;
do not treat its identification of the affected UI as confirmed. Further work
awaits a comparison with the same timed buff on both clients.

---

# Buff cooldown ownership investigation

Reference: local Refuge PRM.exe, SHA256 `7e96f64968558b88d6fe7d4bdc7a12a15231ee30f942159babe54a9c99b1cc90`. Addresses below are VAs
(image base 0x400000). Findings are static disassembly evidence; no live cooldown
capture or screenshot was available to verify the exact reported visual.

## Findings

The existing hook at 0x674BA6 enters 0x66D6D0 under a buff-only scope
(marker +0x3E0 = 'b', flags +0x1BC = 0x201, mode +0x1D4 = 4).
The icon submits two triangles through 0x4A0890, whose queue call at
0x4A0961 is hooked. Those vertices receive the buff anchor and UI scale.

The same native function has a timed-status branch after the icon draws:

- 0x66DAB0 matches the buff ID at +0x3F0 against status records.
- 0x66DAC5 reads the clock and compares status expiry; it excludes zero and
  the sentinel 999999. The branch also handles the alternate game clock.
- 0x66DB6A / 0x66DB75 copy the icon position into the status drawing record.
- 0x66DB8D calls 0xBCEBD0 with half-width/height 16.
- 0xBCEBD0 / 0xBCF120 construct segmented geometry; 0xBCF393 allocates
  a renderer primitive and 0xBCF3C0 loops over 24 vertices with stride 32,
  applying the status position. The primitive is added to a deferred list.
- 0x66DBBB calls 0xBCEB50, which drains that list via 0xBCEB6D ->
  0x4A0550 with flags 0x201. That submission call is NOT hooked.
  A second list drains through 0xBCEBAD -> 0x4A0550; it needs separate
  scope/lifetime review before inclusion.

This establishes a concrete ownership gap for timed buff geometry: the icon
is tagged, while this overlay submission bypasses all current queue hooks.
It is consistent with the reported detached cooldown. It is not evidence
that every kind of cooldown text/overlay uses this path on every client.

There is a second implementation constraint: owner_bitmap_note_vertices
currently rejects owned submissions unless their vertex count is 3 or 4.
Simply adding the missing queue hook will therefore not solve the segmented
24-vertex case.

## Recommended implementation and validation

Hook the validated timed-overlay queue call under the existing buff scope,
and add bounded ownership support for its segmented geometry. Preserve
per-vertex attributes, apply the icon's exact anchor/scale once, and keep
unowned world effects unchanged. Do not enable global or unmatched scaling.
Investigate deferred-list behavior in both display modes before tagging the
second list, so an unrelated overlay cannot inherit the last buff's identity.

Regression coverage must include a 24-vertex timed overlay and its icon at
125%/150%, disabled UI scaling, an unowned overlay, wrong-thread scope,
nested scope restoration, and downstream draw-hook chaining. Validate native
callsite bytes before patching. Live testing should cover multiple timed buffs,
expiration and both cooldown display modes.

The packaged prm-hotbar-settled-fix.zip contains the hotbar correction only;
it does not claim to fix this newly identified cooldown submission gap.

## Implemented producer ownership

The new implementation hooks the buff-specific builder call at 0x66DB8D,
then tags the finished vertices at status-data +0x28 while the icon scope is
still active. This avoids assigning ownership at either shared list flush.
The native constructor confirms count 24 at data +0x0C. Runtime installation
checks that constructor instruction and the builder's vertex address/count
instructions, in addition to validating the direct call target.

The ownership registry now fingerprints all 24 vertices (768 bytes), retaining
its bounded capacity/probing and existing expiry. Draw scratch capacity is
1024 bytes. The original allocation is unchanged; the draw copy receives the
same anchor, scale and offset as the buff icon. Colors, UVs and depth stay intact.
The registry grows by 1,966,080 bytes to retain complete fingerprints.

Validation: test_effect_sprites.py extracts the production builder wrapper,
registry and scaler into an i386 ASan/UBSan fixture. It covers delayed scope
exit, scales 125 through 200, every vertex fingerprint, attributes, source
immutability, consumed ownership, unowned/disabled/transparent cases. Existing
bitmap, native draw thunk and filter tests pass. Native hook verification
matches the local executable. Live screenshots/logs are still required to
confirm both display modes and multiple expiring buffs on the user's client.

Additional deferred regression: three cooldown allocations with independent
transforms are produced first and consumed in reverse order; each retains its
recorded transform. A nonzero but incorrect thread ID is rejected, and an
undrawn overlay expires after the existing two-present grace. These checks
pass under the same i386 ASan/UBSan fixture.
