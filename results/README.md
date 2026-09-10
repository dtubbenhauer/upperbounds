# Crossing-change witnesses

The [results table](bounds.csv) contains 15 witnesses establishing upper
bound 2. Each source reaches its named target, possibly mirrored, by one
crossing change. Explicit one-change unknotting witnesses for all targets
are included. There are 14 distinct targets because `10_131` occurs twice.

| Knot | Target, up to mirror | Crossing index, zero-based | Upper bound | Snapshot lower bound |
| --- | --- | --- | --- | --- |
| [12a_262](certificates/12a_262.json) | 6_3 | 0 | 2 | 2 |
| [13n_1439](certificates/13n_1439.json) | 9_27 | 14 | 2 | 1 |
| [13n_221](certificates/13n_221.json) | 10_84 | 17 | 2 | 1 |
| [13n_2251](certificates/13n_2251.json) | 11a_77 | 24 | 2 | 1 |
| [13n_2379](certificates/13n_2379.json) | 11a_345 | 24 | 2 | 2 |
| [13n_2639](certificates/13n_2639.json) | 11a_146 | 14 | 2 | 1 |
| [13n_2809](certificates/13n_2809.json) | 9_22 | 20 | 2 | 2 |
| [13n_2907](certificates/13n_2907.json) | 10_133 | 19 | 2 | 2 |
| [13n_3033](certificates/13n_3033.json) | 12n_646 | 14 | 2 | 2 |
| [13n_3589](certificates/13n_3589.json) | 10_131 | 19 | 2 | 2 |
| [13n_4025](certificates/13n_4025.json) | 10_26 | 19 | 2 | 1 |
| [13n_45](certificates/13n_45.json) | 10_23 | 19 | 2 | 2 |
| [13n_489](certificates/13n_489.json) | 10_131 | 1 | 2 | 2 |
| [13n_636](certificates/13n_636.json) | 10_91 | 15 | 2 | 1 |
| [13n_80](certificates/13n_80.json) | 10_95 | 18 | 2 | 2 |

The lower bounds shown here are from the KnotInfo snapshot of 8 September
2026; the crossing-change replay verifies upper bounds. Together they give
9 exact values and 6 intervals `[1,2]`. Thirteen of the witnesses improve
the snapshot's upper bounds; `12a_262` and `13n_489` already have value 2
there. This comparison is specific to the snapshot.

## Files and conventions

- `certificates/`: the complete source crossing-change records.
- [source_pds.json](source_pds.json): the source diagrams from the search input.
- [target_witnesses.json](target_witnesses.json): target PDs and their explicit unknotting crossing changes.
- [verification.json](verification.json): saved successful source and target checks, including peripheral maps and package versions.
- [knotinfo_snapshot.json](knotinfo_snapshot.json): the relevant comparison intervals.
- [provenance.json](provenance.json): data, model and software identifiers.
- [SHA256SUMS](SHA256SUMS): checksums for this result folder.

Indices start at zero. Changing crossing `[a,b,c,d]` to `[b,c,d,a]` is the
crossing-change convention used by the replay. Mirrors are permitted
throughout. Source diagrams, inflated diagrams, the changed/reduced
relation, and the named targets are checked independently with
meridian-preserving SnapPy isometries. Each target is then reduced after
its recorded crossing change to zero crossings with exactly one component.

The saved report contains ordinary SnapPy computations, without Sage's
`verified=True` mode. The report's timestamp records when those checks were
performed. Run `python scripts/check_witnesses.py` from the repository root
to replay them. `--static-only` checks checksums and record consistency.

The results table separates run-start bounds, working workbook lower bounds
and snapshot bounds. These lower bounds are inputs to the comparison and
are not independently proved by the upper-bound witnesses.
