#!/usr/bin/env python3
"""Check the newest Phase 3A native UI hit-ownership diagnostic snapshot."""
from pathlib import Path
import re
import sys


REQUIRED_INCIDENT_OWNERS = {'UIBasicInfoWnd', 'UIMenuIconWnd'}


def audit(text):
    starts = list(re.finditer(r'^=== PRM .* Phase (\S+).*$', text, re.M))
    if not starts or starts[-1][1] != '3A':
        return 2, ['REVIEW: No Phase 3A run is the newest run.']
    run = text[starts[-1].start():]
    snapshots = list(re.finditer(r'^OWNER INPUT 3A .*$', run, re.M))
    if not snapshots:
        return 1, ['REVIEW: No F8 snapshot in the newest run.']
    snapshot = run[snapshots[-1].start():]
    issues, notes, infos, owners, hit = [], [], [], set(), None
    if 'OwnerHit hooks: OK query=2 candidate=1' not in run:
        issues.append('Missing native hit-hook startup confirmation.')
    for line in snapshot.splitlines():
        line = line.strip()
        fields = dict(re.findall(r'(\w+)=([^\s]+)', line))
        if line.startswith('OwnerHit hooks='):
            hit = fields
            try:
                assert all(int(fields[n]) > 0 for n in ('hooks', 'queries', 'scoped'))
                assert 0 <= int(fields['scoped']) <= int(fields['queries'])
                assert int(fields['unmatched']) >= 0 and int(fields['rejected']) >= 0
            except (KeyError, ValueError, AssertionError):
                issues.append('Native hit query hooks or selected-owner scopes are inactive/invalid.')
        if line.startswith('owner '):
            class_name = fields.get('class', '')
            try:
                assert class_name
                assert int(fields['inputOrder']) > 0
                if class_name in REQUIRED_INCIDENT_OWNERS:
                    assert fields['nativeSize'] == '0'
                else:
                    assert fields['nativeSize'] in ('0', '1')
                assert re.fullmatch(r'-?\d+,-?\d+', fields['pos'])
                local = re.fullmatch(r'(-?\d+),(-?\d+)\.\.(-?\d+),(-?\d+)', fields['local'])
                assert local
                left, top, right, bottom = (int(value) for value in local.groups())
                assert right > left and bottom > top
                if class_name in REQUIRED_INCIDENT_OWNERS:
                    assert left == 0 and top == 0
                owners.add(class_name)
            except (KeyError, ValueError, AssertionError):
                if class_name in REQUIRED_INCIDENT_OWNERS:
                    issues.append('Invalid Basic Info/menu owner record.')
                elif class_name:
                    issues.append('Invalid owner record for ' + class_name + '.')
                else:
                    issues.append('Invalid owner record.')
        if line.startswith(('OwnerCapture maps=', 'OwnerBitmap hooks=', 'Cursor hooks=', 'WorldInput enabled=')):
            for n in ('unknown', 'overflow', 'expired', 'mismatched', 'capacityLimits', 'walkLimits',
                      'rawFailures'):
                if fields.get(n, '0') != '0':
                    notes.append(line.split()[0] + '.' + n + '=' + fields[n])
            for n in ('unsupported', 'unowned'):
                if fields.get(n, '0') != '0':
                    infos.append(line.split()[0] + '.' + n + '=' + fields[n])
    if hit is None:
        issues.append('Missing native hit-query counters.')
    if not REQUIRED_INCIDENT_OWNERS.issubset(owners):
        issues.append('Basic Info and its icon menu must both be visible for this snapshot.')
    result = ['Phase 3A native UI hit audit; tracked owner classes: ' +
              (', '.join(sorted(owners)) or 'none')]
    result.append('Required incident owners: ' + ', '.join(sorted(REQUIRED_INCIDENT_OWNERS)))
    if hit:
        result.append('Hit queries=' + hit.get('queries', '?') + ', scoped=' + hit.get('scoped', '?') +
                      ', conflicting candidates rejected=' + hit.get('rejected', '?'))
        if hit.get('rejected') == '0':
            result.append('No conflicting native candidate was observed in this run.')
    result += ['REVIEW: ' + issue for issue in dict.fromkeys(issues)]
    result += ['OTHER COUNTER REQUIRES REVIEW: ' + note for note in dict.fromkeys(notes)]
    result += ['INFO: ' + info for info in dict.fromkeys(infos)]
    if not issues and not notes:
        result.append('PASS: native hit ownership is active and Basic Info/menu have input regions.')
    elif not issues:
        result.append('REVIEW: native hit ownership is present, but one or more diagnostic counters are nonzero.')
    result.append('Actual click, button and drag behavior still requires the user result.')
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
