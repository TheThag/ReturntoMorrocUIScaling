#!/usr/bin/env python3
"""Check latest-run minimap ownership; visual placement needs user feedback."""
from pathlib import Path
import re
import sys


def audit(text):
    starts = list(re.finditer(r'^=== PRM .* Phase (\S+).*$', text, re.M))
    if not starts or starts[-1][1] != '2Z':
        return 2, ['No Phase 2Z run is the newest run.']
    run = text[starts[-1].start():]
    names = {'UIMinimapZoomWnd'}
    seen, issues, notes = set(), [], []
    samples = []
    minimap_draws = 0
    for line in run.splitlines():
        line = line.strip()
        fields = dict(re.findall(r'(\w+)=([^\s]+)', line))
        if line.startswith(('owner ', 'visualOnly ')) and fields.get('class') in names:
            try:
                x, y = map(int, fields['pos'].split(','))
                bounds = re.fullmatch(r'0,0\.\.(\d+),(\d+)', fields['local'])
                assert bounds is not None
                w, h = map(int, bounds.groups())
                ax, ay = map(int, fields['anchor'].split(','))
                assert line.startswith('owner ') and int(fields['inputOrder']) > 0
                assert fields['nativeSize'] == '0'
                assert w > 0 and h > 0
                seen.add(fields['class'])
            except (KeyError, ValueError, AssertionError):
                issues.append('Invalid minimap owner bounds or input: ' + line)
        if line.startswith('Minimap draws='):
            try:
                minimap_draws = max(minimap_draws, int(fields['draws']))
            except (ValueError, KeyError):
                issues.append('Invalid minimap draw counter.')
        if line.startswith('OwnerBitmap hooks='):
            samples.append(fields)
        if line.startswith(('WorldInput enabled=', 'Cursor hooks=', 'OwnerCapture maps=', 'UIFilter crisp=')):
            for key in ('rawFailures', 'overflow', 'capacityLimits', 'walkLimits', 'unknown', 'failures'):
                if fields.get(key, '0') != '0':
                    notes.append(line.split()[0] + '.' + key + '=' + fields[key])
        if line.startswith('OwnerCapture limit reason='):
            notes.append(line)
    if not minimap_draws:
        issues.append('No minimap scene activity recorded.')
    if not seen:
        issues.append('No valid minimap owner recorded; press F8 with the minimap visible.')
    if 'OwnerBitmap hooks: OK bitmap=2 overlay=1 special=1 map=1 minimap=1 queue=10 offscreen=2' not in run:
        issues.append('Missing bitmap hook startup confirmation.')
    if not samples:
        issues.append('Missing bitmap F8 counters.')
    for sample in samples:
        try:
            assert all(int(sample[key]) > 0 for key in ('hooks', 'calls', 'matched'))
            assert all(int(sample[key]) == 0 for key in ('overflow', 'expired', 'mismatched'))
        except (KeyError, ValueError, AssertionError):
            issues.append('Incomplete, inactive, or failing bitmap counters.')
    result = ['Phase 2Z minimap audit; scene draws=' + str(minimap_draws) + '; recorded classes: ' + (', '.join(sorted(seen)) or 'none')]
    result += ['REVIEW: ' + item for item in dict.fromkeys(issues)]
    result += ['OTHER COUNTER REQUIRES REVIEW: ' + item for item in dict.fromkeys(notes)]
    if not issues:
        result.append('PASS: minimap scene activity, owner bounds, input records, and bitmap counters.')
    result.append('Minimap image/marker alignment and control interaction require the user result.')
    return int(bool(issues or notes)), result


if __name__ == '__main__':
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.home() / 'Games/Refuge/prm-ui-fix.log'
    try:
        status, lines = audit(path.read_text(errors='replace'))
    except OSError as error:
        print(error, file=sys.stderr)
        sys.exit(2)
    print('\n'.join(lines))
    sys.exit(status)
