# Upper bounds for unknotting numbers

Code, data and crossing-change witnesses for
[RL unknotter, hard unknots and unknotting number](https://arxiv.org/abs/2603.07955).

The repository contains a search notebook, its input workbook and pretrained
PPO model, and **15 checked witnesses giving upper bound 2**. The source
diagrams, crossing indices, target unknotting witnesses and verification
results are included.

## Contents

| File or folder | Purpose |
| --- | --- |
| [notebooks/unknotting.ipynb](notebooks/unknotting.ipynb) | Local candidate search. |
| [notebooks/check_witnesses.ipynb](notebooks/check_witnesses.ipynb) | Witness replay locally or in Google Colab. |
| [scripts/check_witnesses.py](scripts/check_witnesses.py) | Command-line witness replay. |
| [data/unknotting.xlsx](data/unknotting.xlsx) | Search input: diagrams, invariants and working bounds. |
| [models/best_model.zip](models/best_model.zip) | Pretrained PPO reducer. |
| [results/](results/) | Witness table, certificates, target diagrams and saved checks. |
| [data/README.md](data/README.md) | Input definitions, snapshot and search logs. |

## Run the search

Clone or download the repository, then run these commands from its root:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
jupyter lab
```

Open `notebooks/unknotting.ipynb` and run the cells in order. Its configuration
cell controls knot selection, inflation, crossing trials and model handling.
For a short run, set `PROCESS_MODE = "first_n"` and reduce `FIRST_N`.
Dependencies include the pinned V2-enabled Spherogram revision.

**The search writes to `data/unknotting.xlsx`; keep a copy before running.**
Result and invariant-audit JSONL files go to `outputs/`, with working files
in `outputs/upper_bound_improver_work/`. Progress is saved at checkpoints
and normal completion. Work since the last checkpoint can be lost on
interruption. Give distinct experiments different `RUN_LABEL` values.

The search inflates diagrams, changes one crossing and applies preliminary
Reidemeister simplification. It filters candidate targets using **Jones,
Alexander, hyperbolic volume and V2**, allowing mirrors. Required volume or
V2 data must be present. The PPO reducer is used when further reduction may
help. The 15 included witnesses were found in the `pre_rl` phase.

The search proposes `1 + max(target bounds among surviving candidates)`.
Invariant matches and working target bounds need independent support before
this becomes an established bound. The included witness replay checks the
published collection; it does not automatically certify new search results
or every workbook entry.

## Check the witnesses

The checker needs SnapPy but does not load or train the model:

```bash
python -m pip install -r requirements-check.txt
python scripts/check_witnesses.py
```

Or [open the checker in Google Colab](https://colab.research.google.com/github/dtubbenhauer/upperbounds/blob/main/notebooks/check_witnesses.ipynb)
and run all cells. The report is saved to `outputs/witness_checks.json`.

For each source, the checker identifies the source and inflated diagrams,
replays the recorded crossing change, checks the reduced diagram against
the target, and checks an explicit one-crossing unknotting witness for that
target. Identifications use meridian-preserving SnapPy isometries, allowing
mirrors. Target reduction requires **zero crossings and exactly one component**.
Expected result: **15 `PASS_SUPPORTED` records**.

These are ordinary SnapPy computations, without Sage's `verified=True` mode.
Unresolved checks remain unresolved. Saved results and the precise comparison
snapshot are described in [results/README.md](results/README.md).

## References

- [RL unknotter, hard unknots and unknotting number](https://arxiv.org/abs/2603.07955).
- [KnotInfo: Table of Knot Invariants](https://knotinfo.math.indiana.edu/).
- [SnapPy](https://snappy.computop.org/), by Culler, Dunfield, Goerner and Weeks; [isometry documentation](https://snappy.computop.org/manifold.html#snappy.Manifold.is_isometric_to).
- Garoufalidis–Kashaev, *Multivariable knot polynomials from braided Hopf algebras with automorphisms*: [arXiv:2311.11528](https://arxiv.org/abs/2311.11528), [doi:10.4171/PRIMS/62-1-3](https://doi.org/10.4171/PRIMS/62-1-3).
- Garoufalidis–Li, *Patterns of the V2-polynomial of knots*: [arXiv:2409.03557](https://arxiv.org/abs/2409.03557), [doi:10.1080/10586458.2026.2651081](https://doi.org/10.1080/10586458.2026.2651081).

See [LICENSE](LICENSE) for the software license.
