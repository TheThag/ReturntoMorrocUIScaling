#!/usr/bin/env python3
"""Test the bounded, non-executing OptionInfo.lua resolution parser."""

from ctypes import CDLL, POINTER, byref, c_char_p, c_int32, c_uint32
from pathlib import Path
import os
import re
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parent
HEADER = (ROOT / "ui_resolution.h").read_text()


def build_parser(directory: Path):
    (directory / "ui_resolution.h").write_text(HEADER)
    source = r'''
#include <stdint.h>
typedef uint32_t DWORD;
typedef int32_t LONG;
#include "ui_resolution.h"
int parse_resolution(const char* text, DWORD length, LONG* width, LONG* height) {
    return ui_resolution_parse(text, length, width, height);
}
'''
    c_file = directory / "resolution.c"
    shared = directory / "resolution.so"
    c_file.write_text(source)
    subprocess.run([
        os.environ.get("CC", "clang"), "-std=c11", "-O2", "-Wall", "-Wextra",
        "-Werror", "-shared", "-fPIC", str(c_file), "-o", str(shared),
    ], check=True)
    parser = CDLL(str(shared)).parse_resolution
    parser.argtypes = [c_char_p, c_uint32, POINTER(c_int32), POINTER(c_int32)]
    parser.restype = c_int32
    return parser


def call(parser, text, initial=(111, 222), length=None):
    if isinstance(text, str):
        text = text.encode("utf-8")
    if length is None:
        length = len(text)
    width, height = c_int32(initial[0]), c_int32(initial[1])
    result = parser(text, length, byref(width), byref(height))
    return result, (width.value, height.value)


def check(parser, text, expected):
    result, pair = call(parser, text, initial=(7, 9))
    assert result == 1 and pair == expected, (text, result, pair, expected)


def check_failure(parser, text, initial=(111, 222), length=None):
    result, pair = call(parser, text, initial=initial, length=length)
    assert result == 0 and pair == initial, (text, result, pair, initial)


def expected_generated_resolution(data):
    """Derive expected values independently for a generated OptionInfo file."""
    values = {}
    for line in data.decode("utf-8-sig").splitlines():
        match = re.fullmatch(
            r"\s*OptionInfoList\s*\[\s*(['\"])(WIDTH|HEIGHT)\1\s*\]"
            r"\s*=\s*(\d+)\s*;?\s*",
            line,
        )
        if match:
            values[match.group(2)] = int(match.group(3))
    assert set(values) == {"WIDTH", "HEIGHT"}, values
    return values["WIDTH"], values["HEIGHT"]


def main():
    with tempfile.TemporaryDirectory(prefix="prm-resolution-test-") as name:
        parser = build_parser(Path(name))

        # Exercise the real savedata file when it is available.  The expected
        # pair is derived independently from generated assignment lines so the
        # test does not assume a particular user's private display settings.
        if len(sys.argv) > 1:
            actual_path = Path(sys.argv[1])
            actual = actual_path.read_bytes()
            check(parser, actual, expected_generated_resolution(actual))

        check(parser, 'OptionInfoList [ "WIDTH" ] = 1920\r\n'
                      'OptionInfoList [ \'HEIGHT\' ] = 1080;\r\n', (1920, 1080))
        check(parser, b'\xef\xbb\xbfOptionInfoList["WIDTH"] = 3840;\n'
                      b'OptionInfoList["HEIGHT"] = 2160\n', (3840, 2160))
        check(parser, 'OptionInfoList["WIDTH"] = 640\nOptionInfoList["HEIGHT"] = 480', (640, 480))
        check(parser, 'OptionInfoList["WIDTH"] = 16384; OptionInfoList["HEIGHT"] = 16384',
              (16384, 16384))

        # Comments and strings must be opaque to the assignment scanner.
        check(parser, '-- OptionInfoList["WIDTH"] = 1\n'
                      'local s = "OptionInfoList[\\\"HEIGHT\\\"] = 2"\n'
                      '--[[ OptionInfoList["WIDTH"] = 3 ]]\n'
                      '--[=[ OptionInfoList["HEIGHT"] = 4 ]=]\n'
                      '[=[ OptionInfoList["WIDTH"] = 5 ]=]\n'
                      'OptionInfoList["WIDTH"] = 3440 -- tail\n'
                      'OptionInfoList["HEIGHT"] = 1440', (3440, 1440))
        check(parser, 'local a = [[OptionInfoList["WIDTH"] = 1]]\n'
                      'local b = [==[OptionInfoList["HEIGHT"] = 2]==]\n'
                      'OptionInfoList["WIDTH"] = 2560\n'
                      'OptionInfoList["HEIGHT"] = 1440', (2560, 1440))

        # Other keys and near-miss identifiers do not satisfy the exact pair.
        check(parser, 'OptionInfoList["OLD_WIDTH"] = 640\n'
                      'OptionInfoList["OLD_HEIGHT"] = 480\n'
                      'fooOptionInfoList["WIDTH"] = 800\n'
                      'OptionInfoList["WIDTH_EXTRA"] = 801\n'
                      'OptionInfoList["WIDTH"] = 1280\n'
                      'OptionInfoList["HEIGHT"] = 720', (1280, 720))

        # Latest duplicates win; a later invalid duplicate invalidates the
        # dimension instead of silently retaining the earlier value.
        check(parser, 'OptionInfoList["WIDTH"] = 800\n'
                      'OptionInfoList["WIDTH"] = 1920\n'
                      'OptionInfoList["HEIGHT"] = 600\n'
                      'OptionInfoList["HEIGHT"] = 1080', (1920, 1080))
        check(parser, 'OptionInfoList["WIDTH"] = nope;\n'
                      'OptionInfoList["WIDTH"] = 1920\n'
                      'OptionInfoList["HEIGHT"] = 1080', (1920, 1080))
        check_failure(parser, 'OptionInfoList["WIDTH"] = 1920\n'
                             'OptionInfoList["WIDTH"] = 1920 + 1\n'
                             'OptionInfoList["HEIGHT"] = 1080')
        check_failure(parser, 'OptionInfoList["WIDTH"] = 1920\n'
                             'OptionInfoList["WIDTH"] = 639\n'
                             'OptionInfoList["HEIGHT"] = 1080')

        # Expressions, signs, floats, hex, ranges, and truncated values fail.
        for bad in (
            'OptionInfoList["WIDTH"] = 1920 + 0\nOptionInfoList["HEIGHT"] = 1080',
            'OptionInfoList["WIDTH"] = (1920)\nOptionInfoList["HEIGHT"] = 1080',
            'OptionInfoList["WIDTH"] = 1920.0\nOptionInfoList["HEIGHT"] = 1080',
            'OptionInfoList["WIDTH"] = 0x780\nOptionInfoList["HEIGHT"] = 1080',
            'OptionInfoList["WIDTH"] = -1\nOptionInfoList["HEIGHT"] = 1080',
            'OptionInfoList["WIDTH"] = +1920\nOptionInfoList["HEIGHT"] = 1080',
            'OptionInfoList["WIDTH"] = 639\nOptionInfoList["HEIGHT"] = 1080',
            'OptionInfoList["WIDTH"] = 1920\nOptionInfoList["HEIGHT"] = 479',
            'OptionInfoList["WIDTH"] = 16385\nOptionInfoList["HEIGHT"] = 1080',
            'OptionInfoList["WIDTH"] = 1920\nOptionInfoList["HEIGHT"] = 16385',
            'OptionInfoList["WIDTH"] = 1920\nOptionInfoList["HEIGHT"] =',
        ):
            check_failure(parser, bad)

        valid_pair = ('OptionInfoList["WIDTH"] = 1920\n'
                      'OptionInfoList["HEIGHT"] = 1080\n')
        check_failure(parser, valid_pair + 'local text = "unterminated')
        check_failure(parser, valid_pair + '--[[ unterminated')
        check_failure(parser, valid_pair + '[=[ unterminated')

        # Bounded length: a valid-looking tail outside the supplied buffer is
        # invisible, and outputs stay unchanged on partial pairs.
        partial = b'OptionInfoList["WIDTH"] = 1920\nOptionInfoList["HEIGHT"] = 1080'
        cut = partial.index(b'OptionInfoList["HEIGHT"]')
        check_failure(parser, partial, length=cut)
        check_failure(parser, 'OptionInfoList["WIDTH"] = 1920\n')
        check_failure(parser, 'OptionInfoList["WIDTH"] = 1920 HEIGHT = 1080\n')

        print("PASS resolution parser: bounded literal WIDTH/HEIGHT extraction, BOM/CRLF/whitespace, Lua comments and strings, exact keys, ranges, expressions, duplicates, truncation, and atomic outputs")


if __name__ == "__main__":
    main()
