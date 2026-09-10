#!/usr/bin/env python3
"""Replay the crossing-change witnesses without changing the search workbook.

Requires SnapPy 3.3.2. --static-only uses the Python standard library.
Ordinary SnapPy computations are used, without Sage's verified=True mode.
"""
from __future__ import annotations
import argparse
import ast
from collections import Counter
from datetime import datetime, timezone
import csv
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import random
import sys

def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


def read_csv(path):
    with path.open(newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def interval(value):
    if isinstance(value, str) and value.startswith('['):
        return tuple(map(int, ast.literal_eval(value)))
    return (int(float(value)),) * 2


def validate_pd(pd):
    require(isinstance(pd, list) and bool(pd), 'Expected a nonempty PD for a source or target knot')
    require(all(isinstance(q, (list, tuple)) and len(q) == 4 for q in pd), 'Malformed PD quadruple')
    labels = [v for q in pd for v in q]
    require(all(type(v) is int and v >= 0 for v in labels), 'PD labels must be nonnegative integers')
    require(all(v == 2 for v in Counter(labels).values()), 'Each arc label must appear twice')


def flipped_pd(pd, indices):
    validate_pd(pd)
    require(len(indices) == len(set(indices)), 'Duplicate crossing-change indices')
    changed = [list(q) for q in pd]
    for i in indices:
        require(type(i) is int and 0 <= i < len(changed), 'Crossing-change index out of range')
        changed[i] = changed[i][1:] + changed[i][:1]
    return changed


def static_audit(root):
    base = root / 'results'
    hash_count = 0
    for line in (base / 'SHA256SUMS').read_text().splitlines():
        expected, relative = line.split(None, 1)
        path = (base / relative.strip()).resolve()
        require(path.is_relative_to(base.resolve()), 'Checksum path outside results folder')
        require(hashlib.sha256(path.read_bytes()).hexdigest() == expected, 'Checksum mismatch: ' + relative)
        hash_count += 1
    rows = read_csv(base / 'bounds.csv')
    names = [r['knot'] for r in rows]
    require(bool(names) and len(names) == len(set(names)), 'Empty or duplicate witness table')
    require({p.stem for p in (base / 'certificates').glob('*.json')} == set(names), 'Certificate inventory mismatch')
    source_pds = read_json(base / 'source_pds.json')
    require(set(source_pds) == set(names), 'Source PD inventory mismatch')
    snapshot = {r['knot']: r for r in read_json(base / 'knotinfo_snapshot.json')['comparisons']}
    target_rows = read_json(base / 'target_witnesses.json')
    targets = {r['knot']: r for r in target_rows}
    require(len(targets) == len(target_rows), 'Duplicate target witness')
    require(set(targets) == {r['target_up_to_mirror'] for r in rows}, 'Target witness inventory mismatch')
    items = []
    for row in rows:
        name = row['knot']
        require(row['certificate'] == 'certificates/' + name + '.json', 'Unexpected certificate path')
        cert = read_json(base / row['certificate'])
        result = cert['result']
        e = result['evidence']
        require(result['knot'] == name and e in result['improvement_evidence'], 'Source evidence mismatch')
        require(e['phase'] == row['phase'] == 'pre_rl', 'Phase mismatch')
        require(len(e['matched_knots']) == 1, 'Expected one target in this witness')
        target = e['matched_knots'][0]['knot']
        require(target == row['target_up_to_mirror'], 'Target mismatch')
        pd, i = e['pd_used'], e['flip_index']
        changed = flipped_pd(pd, [i])
        validate_pd(e['best_pd']); validate_pd(source_pds[name])
        require(e['crossing_flipped'] == {'index': i, 'quad': pd[i]}, 'Crossing record mismatch')
        require(int(row['flip_index_zero_based']) == i, 'Crossing index mismatch')
        require(int(row['pd_used_crossings']) == len(pd), 'Input crossing count mismatch')
        require(int(row['reduced_crossings']) == len(e['best_pd']), 'Output crossing count mismatch')
        require(e['candidate_upper'] == result['new_upper'] == int(row['upper_bound']) == 2, 'Upper bound mismatch')
        require(e['matched_upper'] == 1, 'Target bound mismatch')
        b = snapshot[name]
        require(b['target'] == target, 'Snapshot target mismatch')
        source_interval = interval(b['current_knotinfo_bounds'])
        require(source_interval == (int(row['knotinfo_2026_09_08_lower']), int(row['knotinfo_2026_09_08_upper'])), 'Snapshot interval mismatch')
        require(interval(b['target_knotinfo_bounds'])[1] == int(row['target_knotinfo_2026_09_08_upper']) == 1, 'Unsupported target bound')
        require(row['strict_improvement_vs_snapshot'] == str(source_interval[1] > 2), 'Snapshot comparison mismatch')
        require(int(row['run_start_lower']) == result['old_lower'] and int(row['run_start_upper']) == result['old_upper'], 'Run-start interval mismatch')
        require(int(row['recorded_workbook_lower']) == cert['current_workbook_lower'], 'Workbook lower mismatch')
        items.append({'knot': name, 'target': target, 'evidence': e,
                      'original_pd': source_pds[name], 'changed_pd': changed})
    for target in targets.values():
        w = target['witness']
        require(target['bound'] == len(w['flip_indices']) == 1, 'Expected one target crossing change')
        require(flipped_pd(w['original_pd'], w['flip_indices']) == w['changed_pd'], 'Target changed PD mismatch')
        require(w['final_pd'] == [] and w['unlinked_unknot_components'] == 1, 'Stored target endpoint is not one unknot')
    return items, targets, {'status': 'PASS_STATIC', 'sha256_files': hash_count,
                            'witnesses': len(rows), 'target_witnesses': len(targets)}


def topology_audit(items, targets):
    import snappy

    def components(link):
        return len(link.link_components) + int(link.unlinked_unknot_components)

    def knot_link(pd):
        validate_pd(pd)
        link = snappy.Link(pd)
        require(components(link) == 1, 'Expected exactly one knot component')
        return link

    def exterior(pd):
        return knot_link(pd).exterior()

    def named(name):
        return snappy.Link(name.replace('a_', 'a').replace('n_', 'n')).exterior()

    def compare(first, second):
        errors = []
        a, b = first.copy(), second.copy()
        for attempt in range(3):
            try:
                aa, bb = (a, b) if attempt == 0 else (a.high_precision(), b.high_precision())
                # No orientation restriction: unknotting number is mirror invariant.
                good = [iso for iso in aa.is_isometric_to(bb, return_isometries=True)
                        if iso.extends_to_link()]
                if good:
                    maps = [[[[int(m[i, j]) for j in range(2)] for i in range(2)]
                             for m in iso.cusp_maps()] for iso in good]
                    return {'status': 'PASS_SNAPPY', 'attempt': attempt,
                            'meridian_preserving_cusp_maps': maps}
                errors.append('No meridian-preserving isometry found')
            except Exception as exc:
                errors.append(str(exc))
            if attempt < 2:
                a.randomize()
                b.randomize()
        return {'status': 'UNRESOLVED', 'errors': errors}

    target_results = {}
    for name, target in sorted(targets.items()):
        try:
            w = target['witness']
            identification = compare(exterior(w['original_pd']), named(name))
            link = knot_link(flipped_pd(w['original_pd'], w['flip_indices']))
            link.simplify('global')
            is_unknot = (len(link.crossings) == 0 and components(link) == 1
                         and int(link.unlinked_unknot_components) == 1)
            passed = is_unknot and identification['status'] == 'PASS_SNAPPY'
            row = {'status': 'PASS_TARGET' if passed else 'UNRESOLVED',
                   'identification': identification,
                   'crossings_remaining': len(link.crossings),
                   'total_components': components(link),
                   'unlinked_unknot_components': int(link.unlinked_unknot_components)}
        except Exception as exc:
            row = {'status': 'UNRESOLVED', 'error': str(exc)}
        target_results[name] = row
        print('Target', name, row['status'], flush=True)

    results = []
    for item in items:
        name, target, e = item['knot'], item['target'], item['evidence']
        row = {'knot': name, 'target': target}
        try:
            source_manifold, target_manifold = named(name), named(target)
            reduced = exterior(e['best_pd'])
            checks = {
                'workbook_pd_to_named_source': compare(exterior(item['original_pd']), source_manifold),
                'inflated_pd_to_named_source': compare(exterior(e['pd_used']), source_manifold),
                'changed_pd_to_reduced_pd': compare(exterior(item['changed_pd']), reduced),
                'reduced_pd_to_named_target': compare(reduced, target_manifold),
            }
            row['identifications'] = checks
            topology_pass = all(x['status'] == 'PASS_SNAPPY' for x in checks.values())
            dependency_pass = target_results[target]['status'] == 'PASS_TARGET'
            row['status'] = 'PASS_SUPPORTED' if topology_pass and dependency_pass else 'UNRESOLVED'
            row['supported_upper'] = 2 if row['status'] == 'PASS_SUPPORTED' else None
        except Exception as exc:
            row.update(status='UNRESOLVED', error=str(exc))
        results.append(row)
        print('Source', name, row['status'], flush=True)
    return {'snappy_version': snappy.__version__,
            'spherogram_version': importlib.metadata.version('spherogram'),
            'targets': target_results, 'sources': results}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo-root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--output', type=Path)
    parser.add_argument('--static-only', action='store_true')
    args = parser.parse_args()
    root = args.repo_root.resolve()
    output = args.output or root / 'outputs/witness_checks.json'
    report = {'created_utc': datetime.now(timezone.utc).isoformat(),
              'python_version': platform.python_version(),
              'mode': 'static_only' if args.static_only else 'ordinary_snappy',
              'scope': 'Witness collection, allowing mirrors; no Sage verified=True mode; no workbook-wide bound audit.'}
    success = False
    try:
        items, targets, report['static'] = static_audit(root)
        if args.static_only:
            success = True
            report['status'] = 'PASS_STATIC_ONLY'
        else:
            random.seed(20260908)
            report['topology'] = topology_audit(items, targets)
            counts = Counter(row['status'] for row in report['topology']['sources'])
            success = counts['PASS_SUPPORTED'] == len(items)
            report['counts'] = dict(counts)
            report['status'] = 'PASS_WITNESSES' if success else 'UNRESOLVED_CHECKS'
    except Exception as exc:
        report.update(status='CHECK_ERROR', error=f'{type(exc).__name__}: {exc}')
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(report['status'], '—', output, flush=True)
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
