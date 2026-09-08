#!/usr/bin/env python3
"""Check the newest UI FIX screen-bounds diagnostic snapshot."""
from pathlib import Path
import re
import sys


def audit(text):
    runs = list(re.finditer(r'^=== PRM .* Phase (\S+).*$', text, re.M))
    if not runs or runs[-1][1] != '3B':
        return 2, ['REVIEW: The newest run is not Phase 3B.']
    run = text[runs[-1].start():]
    samples = list(re.finditer(r'^OWNER INPUT 3B .*$', run, re.M))
    if not samples:
        return 1, ['REVIEW: No F8 snapshot in the newest run.']
    sample = run[samples[-1].start():]
    issues, owners, settings, hit = [], [], None, None
    for line in sample.splitlines():
        line = line.strip()
        fields = dict(re.findall(r'(\w+)=([^\s]+)', line))
        if line.startswith('UISettings '):
            settings = fields
        elif line.startswith('OwnerHit '):
            hit = fields
        elif line.startswith('owner '):
            owners.append(fields)
        elif line.startswith(('OwnerCapture maps=', 'OwnerBitmap hooks=', 'Cursor hooks=', 'WorldInput enabled=')):
            for key in ('unknown', 'overflow', 'expired', 'mismatched', 'capacityLimits', 'walkLimits', 'rawFailures'):
                if fields.get(key, '0') != '0':
                    issues.append(line.split()[0] + '.' + key + '=' + fields[key])
    width = height = 0
    try:
        assert settings and settings['enabled'] == settings['keepOnScreen'] == '1'
        width, height = map(int, settings['screen'].split('x'))
        assert width > 0 and height > 0 and 100 <= int(settings['scale']) <= 200
    except (KeyError, ValueError, AssertionError):
        issues.append('Missing/invalid screen settings, or scaling/KeepOnScreen is disabled.')
    try:
        assert hit and hit['hooks'] == '1' and int(hit['queries']) > 0
        assert 0 <= int(hit['scoped']) <= int(hit['queries'])
    except (KeyError, ValueError, AssertionError):
        issues.append('Missing/invalid native hit ownership activity.')
    checked = []
    for owner in owners:
        name = owner.get('class', '?')
        # Actor-attached room titles follow actors; fullscreen maps keep native coordinates.
        if name == 'UIChatRoomTitle' or owner.get('nativeSize') == '1':
            continue
        try:
            match = re.fullmatch(r'(-?\d+),(-?\d+)\.\.(-?\d+),(-?\d+)', owner['display'])
            assert match and name != '?' and int(owner['inputOrder']) > 0
            left, top, right, bottom = map(int, match.groups())
            assert 0 < int(owner['fitPercent']) <= int(settings['scale'])
            assert left < right and top < bottom
            assert left >= -1 and top >= -1 and right <= width + 1 and bottom <= height + 1
            checked.append(name)
        except (KeyError, TypeError, ValueError, AssertionError):
            issues.append('Invalid or out-of-screen input region: ' + name)
    if not checked:
        issues.append('No ordinary fitted input window was observed.')
    lines = ['Phase 3B bounds audit: ' + str(len(checked)) + ' fitted windows checked.']
    lines += ['REVIEW: ' + issue for issue in dict.fromkeys(issues)]
    if not issues:
        lines.append('PASS: sampled window bounds fit the screen and native input ownership is active.')
    lines.append('F2 panel operation, toggles, clicks and drag smoothness still require the user result.')
    return int(bool(issues)), lines


if __name__ == '__main__':
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.home() / 'Games/Refuge/prm-ui-fix.log'
    try:
        status, lines = audit(path.read_text(errors='replace'))
    except OSError as error:
        print(error, file=sys.stderr)
        sys.exit(2)
    print('\n'.join(lines))
    sys.exit(status)
