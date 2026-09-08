#!/usr/bin/env python3
"""Check scoped hook RVAs against the exact PRM PE image and C constants.

Usage: python3 verify_hooks.py [path/to/PRM.exe] [--source path/to/prm_uifix.c]
No disassembler or third-party Python packages are required. All addresses in
the manifest are relative to the image base, never the .text section base.
"""

import argparse
from pathlib import Path
import re
import struct
import sys


HOOKS = (
    ("UI event hit query", "PRM_UI_HIT_EVENT", 0x001F862C, 0x001FA1A0),
    ("UI mouse hit query", "PRM_UI_HIT_MOUSE", 0x00209FCE, 0x001FA1A0),
    ("World ray", "PRM_WORLD_RAY", 0x00334568, 0x000A1540),
    ("Cursor draw", "PRM_CURSOR_DRAW", 0x00227B7B, 0x00227BC0),
    ("Sprite submit", "PRM_SPRITE_SUBMIT", 0x00227FD9, 0x000A0550),
    ("Bitmap submit", "PRM_BITMAP_QUEUE", 0x000AB5A1, 0x000A0550),
    ("Window overlay draw", "PRM_OVERLAY_DRAW", 0x0020BAF0, 0x0071C8C0),
    ("Window overlay submit", "PRM_OVERLAY_QUEUE", 0x0071C8DD, 0x000A0550),
    ("Special window draw", "PRM_SPECIAL_DRAW", 0x0020BA73, 0x0017B6B0),
    ("Map region overlay", "PRM_MAP_DRAW", 0x0020BA38, 0x0017B3E0),
    ("Compact minimap scene draw", "PRM_MINIMAP_DRAW", 0x0034024D, 0x00331E70),
    ("Minimap image and marker submit", "PRM_MINIMAP_QUEUE", 0x0022835F, 0x000A0550),
    ("Minimap direction marker submit", "PRM_MINIMAP_MARKER_QUEUE", 0x003325C4, 0x000A0550),
    ("Screen rectangle submit", "PRM_RECT_QUEUE", 0x0009277F, 0x000A0550),
    ("Screen image submit", "PRM_IMAGE_QUEUE", 0x00093058, 0x000A0550),
    ("Map preview texture submit", "PRM_PREVIEW_QUEUE", 0x000AB829, 0x000A0550),
    ("Map line submit", "PRM_MAP_LINE_QUEUE", 0x00091FD0, 0x000A0550),
    ("Map route arrow submit", "PRM_MAP_ARROW_QUEUE", 0x00177DC0, 0x000A0550),
    ("Map character marker submit", "PRM_MAP_SPRITE_QUEUE", 0x0017AA2D, 0x000A0550),
)

# Each manager thunk replaces one indirect thiscall plus the following EBX
# restore. The six-byte span ends exactly at the native continuation.
BITMAP_PATCHES = (
    ("Primary window bitmap", "PRM_BITMAP_PRIMARY_RVA", 0x0020BAD4,
     bytes.fromhex("ff 53 28 8b 5d dc")),
    ("Alternate window bitmap", "PRM_BITMAP_ALTERNATE_RVA", 0x0020BAA3,
     bytes.fromhex("ff 53 0c 8b 5d dc")),
)

# Replace only the manager's root candidate call, preserving the original
# per-window +B8 virtual method and its recursive child/control hit tests.
INPUT_PATCHES = (
    ("Native UI root hit candidate", "PRM_UI_HIT_CANDIDATE_RVA", 0x001FA1C2,
     bytes.fromhex("ff 90 b8 00 00 00")),
)
INPUT_RETURNS = (
    ("Central mouse ScreenToClient", "PRM_UI_MOUSE_RETURN_RVA", 0x00495BE1,
     bytes.fromhex("ff 15 70 74 d0 00")),
)

# These return addresses identify the direct D3D calls used to assemble a
# cached window texture offscreen. They must bypass screen-space transforms.
# Check the entire preceding call, not merely the return-address constant.
OFFSCREEN_RETURNS = (
    ("Offscreen DrawPrimitive", "PRM_OFFSCREEN_DP_RETURN_RVA", 0x000A22A1,
     bytes.fromhex("ff 57 64")),
    ("Offscreen DrawIndexedPrimitive", "PRM_OFFSCREEN_DIP_RETURN_RVA", 0x000A228D,
     bytes.fromhex("ff 57 68")),
)

# The viewport setter at image RVA 0xA7ED0 receives full width and height.
# These adjacent instructions store the full values at +0x24/+0x28 and
# shift by one before storing half values at +0x2C/+0x30.
VIEWPORT_STORES = (
    (0x000A7EF4, bytes.fromhex("89 71 28 d1 f8 89 45 f8 89 41 2c")),
    (0x000A7F0A, bytes.fromhex("89 79 24 8b d8 d1 fb 89 59 30")),
)

# Minimap scene draw tests this exact UIWindowMgr+1A8 global. The factory
# stores UIMinimapZoomWnd there; verify the native load and our lookup RVA.
MINIMAP_OWNER = (0x00331E9F, bytes.fromhex("83 3d 80 78 eb 00 00"), 0x00AB7880)


# Native layout evidence for the separately registered Basic Info/menu block.
# No new patch uses these addresses; they validate the object ID and placement.
CONNECTED_LAYOUT = (
    (0x001FF205, bytes.fromhex("68 33 01 00 00 b9 d8 76 eb 00")),
    (0x001FF237, bytes.fromhex("8b 43 18 8b ce 03 45 e0 8b 16 50 ff 75 dc 8b 42 10 ff d0")),
    (0x006CF733, bytes.fromhex("8b 45 08 89 41 1c 8b 45 0c 83 c0 fc 89 41 20")),
    (0x00206ADF, bytes.fromhex("89 43 2c")),
)

# Exact popup constructors and registration, including the classes that have
# no Wnd/Window suffix. These are evidence spans, not additional hooks.
POPUP_LAYOUT = (
    (0x000DCD25, bytes.fromhex("c7 06 f0 1c d3 00")),
    (0x00228500, bytes.fromhex("e8 7b c8 fc ff")),
    (0x0019F974, bytes.fromhex("c7 06 8c cd d3 00")),
    (0x0019F9AB, bytes.fromhex("e8 d0 53 05 00")),
    (0x002284E2, bytes.fromhex("89 47 1c")),
    (0x0019F9B8, bytes.fromhex("68 70 fe ff ff 68 70 fe ff ff")),
)

PLAYER_GAUGE_LAYOUT = (
    (0x000F835D, bytes.fromhex("c7 06 8c 41 d3 00")),
    (0x00351334, bytes.fromhex("89 87 c8 02 00 00")),
    (0x00342788, bytes.fromhex("83 bb c8 02 00 00 00")),
    (0x003427A3, bytes.fromhex("8b 86 ac 00 00 00 83 e8 1e 8b be b0 00 00 00")),
)


class PEImage:
    def __init__(self, path):
        self.data = path.read_bytes()
        if self.read_file(0, 2) != b"MZ":
            raise ValueError("missing DOS MZ header")
        pe = self.unpack("<I", 0x3C)[0]
        if self.read_file(pe, 4) != b"PE\0\0":
            raise ValueError("missing PE signature")
        machine, count = self.unpack("<HH", pe + 4)
        optional_size = self.unpack("<H", pe + 20)[0]
        optional = pe + 24
        if machine != 0x14C or self.unpack("<H", optional)[0] != 0x10B:
            raise ValueError("expected an i386 PE32 image")
        if optional_size < 64:
            raise ValueError("truncated PE32 optional header")
        self.image_base = self.unpack("<I", optional + 28)[0]
        self.sections = []
        for index in range(count):
            at = optional + optional_size + index * 40
            section = self.read_file(at, 40)
            name = section[:8].split(b"\0", 1)[0].decode("ascii", "replace")
            virtual_size, rva, raw_size, raw_offset = struct.unpack_from("<IIII", section, 8)
            flags = struct.unpack_from("<I", section, 36)[0]
            self.sections.append((name, rva, virtual_size, raw_size, raw_offset, flags))

    def read_file(self, offset, size):
        if offset < 0 or size < 0 or offset + size > len(self.data):
            raise ValueError(f"file range 0x{offset:X}+0x{size:X} is out of bounds")
        return self.data[offset:offset + size]

    def unpack(self, fmt, offset):
        return struct.unpack(fmt, self.read_file(offset, struct.calcsize(fmt)))

    def read_code(self, rva, size):
        for name, start, virtual_size, raw_size, raw_offset, flags in self.sections:
            if start <= rva < start + max(virtual_size, raw_size):
                delta = rva - start
                if not flags & 0x20000000:
                    raise ValueError(f"RVA 0x{rva:08X} is in non-executable section {name}")
                if delta + size > raw_size:
                    raise ValueError(f"RVA 0x{rva:08X} is not fully backed by section data")
                return self.read_file(raw_offset + delta, size)
        raise ValueError(f"RVA 0x{rva:08X} is outside all sections")


def source_constant(source, name):
    definitions = re.findall(r"^\s*#\s*define\s+" + re.escape(name) + r"\s+([^\n]+)", source, re.M)
    if len(definitions) != 1:
        raise ValueError(f"expected one #define {name}, found {len(definitions)}")
    literal = re.fullmatch(r"\s*\(?\s*(0[xX][0-9a-fA-F]+|[0-9]+)[uUlL]*\s*\)?\s*", definitions[0])
    if not literal:
        raise ValueError(f"{name} must use an integer literal")
    value = literal[1]
    return int(value, 16 if value.lower().startswith("0x") else 10)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("exe", nargs="?", type=Path, default=Path.home() / "Games/Refuge/PRM.exe")
    parser.add_argument("--source", type=Path, default=Path(__file__).resolve().with_name("prm_uifix.c"))
    args = parser.parse_args()
    try:
        pe = PEImage(args.exe)
        source = args.source.read_text()
    except (OSError, ValueError, struct.error) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1
    source = re.sub(r"/\*.*?\*/|//[^\n]*", "", source, flags=re.S)
    failures = []
    print(f"Executable: {args.exe} (image base 0x{pe.image_base:08X})")
    print(f"Source: {args.source}")
    minimap_rva, minimap_bytes, owner_rva = MINIMAP_OWNER
    try:
        if pe.read_code(minimap_rva, len(minimap_bytes)) != minimap_bytes:
            raise ValueError("Minimap owner: native manager pointer check differs")
        if source_constant(source, "PRM_MINIMAP_WINDOW_RVA") != owner_rva:
            raise ValueError("Minimap owner: source pointer RVA differs")
        print("Minimap owner: native UIWindowMgr+1A8 reference and source RVA match")
    except ValueError as error:
        failures.append(str(error))
    try:
        if pe.read_code(0x000E9290, 6) != bytes.fromhex("8b 0d 8c 8d e7 00"):
            raise ValueError("Tooltip source controller: native load differs")
        if source_constant(source, "PRM_TOOLTIP_MANAGER_RVA") != 0x00A78D8C:
            raise ValueError("Tooltip source controller: source RVA differs")
        print("Tooltip controller: native reference and source RVA match")
    except ValueError as error:
        failures.append(str(error))
    for label, prefix, call_rva, expected_target in HOOKS:
        try:
            instruction = pe.read_code(call_rva, 5)
            if instruction[0] != 0xE8:
                raise ValueError(f"RVA 0x{call_rva:08X}: expected E8, found {instruction[0]:02X}")
            target = call_rva + 5 + struct.unpack("<i", instruction[1:])[0]
            pe.read_code(target, 1)
            print(f"{label}: executable RVA 0x{call_rva:08X} -> 0x{target:08X}; expected 0x{expected_target:08X}")
            if target != expected_target:
                failures.append(f"{label}: executable target differs from manifest")
        except ValueError as error:
            failures.append(f"{label}: {error}")
        for suffix, expected in (("CALL_RVA", call_rva), ("TARGET_RVA", expected_target)):
            name = f"{prefix}_{suffix}"
            try:
                value = source_constant(source, name)
                print(f"  {name}: source 0x{value:08X}; expected 0x{expected:08X}")
                if value != expected:
                    failures.append(f"{name}: source differs from validated executable manifest")
            except ValueError as error:
                failures.append(str(error))
    for entries, is_return in ((BITMAP_PATCHES, False), (INPUT_PATCHES, False),
                              (OFFSCREEN_RETURNS, True), (INPUT_RETURNS, True)):
        for label, name, rva, expected_bytes in entries:
            code_rva = rva - len(expected_bytes) if is_return else rva
            try:
                actual = pe.read_code(code_rva, len(expected_bytes))
                if actual != expected_bytes:
                    raise ValueError(
                        f"{label}: native bytes differ at RVA 0x{code_rva:08X}; "
                        f"found {actual.hex(' ')}, expected {expected_bytes.hex(' ')}")
                print(f"{label}: native instruction bytes at RVA 0x{code_rva:08X}: OK")
            except ValueError as error:
                failures.append(str(error))
            try:
                value = source_constant(source, name)
                print(f"  {name}: source 0x{value:08X}; expected 0x{rva:08X}")
                if value != rva:
                    failures.append(f"{name}: source differs from validated executable manifest")
            except ValueError as error:
                failures.append(str(error))
    for rva, expected in CONNECTED_LAYOUT:
        try:
            if pe.read_code(rva, len(expected)) != expected:
                raise ValueError(f"connected Basic Info/menu layout differs at RVA 0x{rva:08X}")
        except ValueError as error:
            failures.append(str(error))
    print("Connected Basic Info/menu native ID and layout evidence checked")
    for rva, expected in POPUP_LAYOUT:
        try:
            if pe.read_code(rva, len(expected)) != expected:
                raise ValueError(f"transient popup constructor/registration differs at RVA 0x{rva:08X}")
        except ValueError as error:
            failures.append(str(error))
    print("Transient explanation and character-info popup native ownership checked")
    for rva, expected in PLAYER_GAUGE_LAYOUT:
        try:
            if pe.read_code(rva, len(expected)) != expected:
                raise ValueError(f"player gauge constructor/live placement differs at RVA 0x{rva:08X}")
        except ValueError as error:
            failures.append(str(error))
    print("Player HP/SP gauge native constructor and live projection checked")
    viewport_ok = True
    for rva, expected in VIEWPORT_STORES:
        try:
            actual = pe.read_code(rva, len(expected))
            if actual != expected:
                raise ValueError(f"viewport setter bytes differ at RVA 0x{rva:08X}")
        except ValueError as error:
            viewport_ok = False
            failures.append(str(error))
    if viewport_ok:
        print("Viewport setter: full width/height +0x24/+0x28; half width/height +0x2C/+0x30: OK")
    for failure in failures:
        print(f"FAIL: {failure}", file=sys.stderr)
    if failures:
        return 1
    print(f"PASS: {len(HOOKS)} direct callsites, {len(BITMAP_PATCHES)} bitmap patch spans, "
          f"{len(INPUT_PATCHES)} input patch span, {len(OFFSCREEN_RETURNS)} offscreen returns, "
          f"{len(INPUT_RETURNS)} mouse return, source RVAs, and viewport fields match.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
