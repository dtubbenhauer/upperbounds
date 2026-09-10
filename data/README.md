# Data

`unknotting.xlsx` contains 13,756 rows: the unknot, 12,965 nontrivial prime
knots and 790 composite entries. Its columns contain knot names, PD diagrams,
Jones and Alexander vectors, hyperbolic volumes, V2 vectors and working
unknotting-number intervals. The search notebook updates the interval cells.

The workbook is candidate-search input. Only the witnesses listed in
[results/bounds.csv](../results/bounds.csv) are covered by the accompanying
checks. Other working bounds, including target bounds propagated during a
search, require their own evidence. The replay does not establish the
workbook's lower bounds or composite-knot bounds.

`knotinfo_2026-09-08.xls.zip` contains the KnotInfo download of 8 September
2026. Its relevant source and target intervals are also recorded in
[results/knotinfo_snapshot.json](../results/knotinfo_snapshot.json).
This is the comparison snapshot used by the results table.

`search_run.zip` contains candidate result records in `results.jsonl` and
invariant-audit records in `match_audit.jsonl`. The certificate field
`source_line_1_based` points to the result record inside this archive;
`source_archive` is a path relative to the repository root. Log flags such
as `improved` describe candidate search outcomes. Consult the results table
for the witnesses supported by the accompanying checks.

Input and model hashes are recorded in
[results/provenance.json](../results/provenance.json).
