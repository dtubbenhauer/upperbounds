# Upper bounds for unknotting numbers

This repository contains supplementary computational material for the paper

> RL unknotter, hard unknots and unknotting number

The arXiv version is available at

> [arXiv:2603.07955](https://arxiv.org/abs/2603.07955)

The repository contains two main notebooks:

1. [notebooks/unknotting.ipynb](notebooks/unknotting.ipynb), a local notebook
   for searching for crossing changes that improve upper bounds on unknotting
   numbers;
2. [notebooks/check_witnesses.ipynb](notebooks/check_witnesses.ipynb), a notebook
   for checking the resulting witnesses locally or in Google Colab.

The goal is transparency: the repository includes the search input, the
pretrained PPO model, and 15 checked witnesses giving upper bound 2. The source
diagrams, crossing indices, target unknotting witnesses and verification
results are all included.

## Contact

If you find any errors in the paper or code, **please email me**:

[dtubbenhauer@gmail.com](mailto:dtubbenhauer@gmail.com?subject=GitHub%20upperbounds)

Same goes for any errors related to this page.

## Main files

### `notebooks/unknotting.ipynb`

This notebook is the recommended entry point for the search. It is meant to
run locally in Jupyter, using the input workbook `data/unknotting.xlsx` and
the pretrained model `models/best_model.zip`.

The notebook inflates a knot diagram, changes one crossing, and applies
preliminary Reidemeister simplification. It then filters candidate targets
using the Jones polynomial, the Alexander polynomial, hyperbolic volume and
the V2 polynomial, allowing mirrors. Required volume and V2 data must be
present. The PPO reducer is used when further reduction may help.

If the surviving candidates have working upper bounds $U(L)$, the proposed
bound for the source is

$$
    1+\max\{U(L):L\text{ survives the required tests}\}.
$$

The invariant matches and the target bounds need independent support before
this becomes an established upper bound. The witness checker covers the
published collection; it does not automatically certify new search results
or every entry in the workbook.

The 15 included witnesses were found in the `pre_rl` phase, before the PPO
reducer was called for those trials.

### `notebooks/check_witnesses.ipynb`

This notebook checks the included crossing-change witnesses. It can be run
locally or in Google Colab. It uses SnapPy and does not load or train the PPO
model.

For each source, the checker identifies the source and inflated diagrams,
replays the recorded crossing change, and checks the reduced diagram against
the named target. It also checks an explicit one-crossing unknotting witness
for that target.

The identifications use meridian-preserving SnapPy isometries, allowing
mirrors. A target reduction is accepted only when it reaches zero crossings
with exactly one component.

The computations use ordinary SnapPy, without Sage's `verified=True` mode.
Unresolved checks remain unresolved. The saved checks and the comparison
snapshot are described in [results/README.md](results/README.md).

The same calculation can be run from the command line using
`scripts/check_witnesses.py`.

## Requirements

For the search, clone or download the repository and run the following
commands from its root:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
jupyter lab
```

The dependencies include the pinned V2-enabled Spherogram revision.

For the witness checker alone, install the smaller set of requirements:

```bash
python -m pip install -r requirements-check.txt
```

## Examples

Open `notebooks/unknotting.ipynb` in Jupyter and run the cells from top to
bottom. The configuration cell controls knot selection, inflation, crossing
trials and model handling. For a short run, set `PROCESS_MODE = "first_n"`
and reduce `FIRST_N`.

To check the included witnesses, run

```bash
python scripts/check_witnesses.py
```

Alternatively, [open the checker in Google Colab](https://colab.research.google.com/github/dtubbenhauer/upperbounds/blob/main/notebooks/check_witnesses.ipynb)
and run all cells. The expected result is 15 `PASS_SUPPORTED` records. The
report is saved to `outputs/witness_checks.json`.

## Saving the search

The search writes to `data/unknotting.xlsx`, so **keep a copy before running**.
Result and invariant-audit JSONL files are written to `outputs/`. Working
files are stored in `outputs/upper_bound_improver_work/`.

Progress is saved at checkpoints and at normal completion. Work since the
last checkpoint can be lost if the run is interrupted. Give distinct
experiments different `RUN_LABEL` values.

## References

- [RL unknotter, hard unknots and unknotting number](https://arxiv.org/abs/2603.07955).
- [KnotInfo: Table of Knot Invariants](https://knotinfo.math.indiana.edu/).
- [SnapPy](https://snappy.computop.org/), by Culler, Dunfield, Goerner and Weeks; see also the [isometry documentation](https://snappy.computop.org/manifold.html#snappy.Manifold.is_isometric_to).
- Garoufalidis–Kashaev, *Multivariable knot polynomials from braided Hopf algebras with automorphisms*: [arXiv:2311.11528](https://arxiv.org/abs/2311.11528), [doi:10.4171/PRIMS/62-1-3](https://doi.org/10.4171/PRIMS/62-1-3).
- Garoufalidis–Li, *Patterns of the V2-polynomial of knots*: [arXiv:2409.03557](https://arxiv.org/abs/2409.03557), [doi:10.1080/10586458.2026.2651081](https://doi.org/10.1080/10586458.2026.2651081).

## Repository contents

| File or folder | Contents |
| --- | --- |
| [notebooks/unknotting.ipynb](notebooks/unknotting.ipynb) | The local search notebook. |
| [notebooks/check_witnesses.ipynb](notebooks/check_witnesses.ipynb) | The witness checker for local use or Google Colab. |
| [scripts/check_witnesses.py](scripts/check_witnesses.py) | The command-line witness checker. |
| [data/unknotting.xlsx](data/unknotting.xlsx) | Diagrams, invariants and working bounds for the search. |
| [models/best_model.zip](models/best_model.zip) | The pretrained PPO reducer. |
| [results/](results/) | The witness table, certificates, target diagrams and saved checks. |
| [data/README.md](data/README.md) | Input definitions, the comparison snapshot and search logs. |

The software license is in [LICENSE](LICENSE).
