# AGENTS Guidelines for This Repository

This repository (`upperbounds`) contains the code accompanying the paper
*RL unknotter, hard unknots and unknotting number* (arXiv:2603.07955). It
improves upper bounds on unknotting numbers using a reinforcement-learning
based reducer over knot diagrams. The repository follows a library-first
architecture: reusable functionality lives under `src/`, notebooks orchestrate
experiments, and generated artifacts are kept separate from source code.

## 1. Project Overview
- Current notebook workflow lives in
  `notebooks/upper_bound_unknotting_v6_local.ipynb` (the maintained,
  local-only version) and
  `notebooks/upper_bound_unknotting_v5_original.ipynb` (prior version, kept
  for reference).
- Reusable Python code lives under `src/upperbounds/`; notebooks should import
  shared behavior instead of duplicating setup, parsing, I/O, or checkpoint
  logic.
- The notebook: loads `data/unknotting.xlsx` -> fills missing Jones vectors
  from PD presentations -> finds unresolved `[a,b]` unknotting-number ranges
  -> inflates the PD diagram -> flips crossings one at a time -> runs the RL
  unknotter -> recomputes the Jones vector -> matches against the workbook
  (allowing mirrors) -> tightens the upper bound while preserving the lower
  bound -> overwrites `data/unknotting.xlsx`.
- Repository layout:
  ```
  src/             reusable package code imported by notebooks
  data/            unknotting.xlsx (input/output database)
  models/          best_model.zip (pretrained RL model)
  notebooks/       orchestration, exploration, and analysis notebooks
  training_data/   optional hard/random unknot CSV inputs
  outputs/         local generated artifacts, ignored unless intentional
  ```
- `data/unknotting.xlsx` and `models/best_model.zip` are treated as data/build
  artifacts, not source — an agent should not hand-edit them; they're
  produced/consumed by the notebook.

## 2. Setup
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
Key dependencies: `numpy`, `pandas`/`openpyxl`/`xlrd` (Excel I/O), `torch`,
`gymnasium` + `stable-baselines3` (RL), `snappy`/`spherogram`/`plink`/
`snappy-manifolds`/`low-index`/`FXrays`/`cypari` (knot theory / SnapPy
ecosystem), `networkx`, `sympy`, `matplotlib`/`Pillow` (plotting), `jupyterlab`.

Launch with:
```bash
jupyter lab
```
then run `notebooks/upper_bound_unknotting_v6_local.ipynb` top to bottom.
Configuration knobs live in the config cell near the top of the notebook —
check there before assuming a parameter is hardcoded elsewhere.

The notebook looks for a pretrained model in this order: `models/best_model.zip`
-> `models/ppo_knot_rl_spherogram_continued.zip` -> `outputs/best_model.zip`.
Since `models/best_model.zip` is already checked in, retraining is optional.

## 3. Testing & Validation
There is no formal test suite (`pytest`) in this repo — validation is done by
executing the notebook and checking outputs. When an agent changes notebook
code or supporting logic:
- Run the notebook end-to-end (e.g. `jupyter nbconvert --to notebook --execute
  notebooks/upper_bound_unknotting_v6_local.ipynb`) and confirm it completes
  without errors.
- Sanity-check that `data/unknotting.xlsx` updates only *tighten* upper
  bounds and never violate the existing lower bound (e.g. `[2,3] -> [2,2]` is
  valid, widening a range is not).
- If you add a `.py` module outside the notebooks, add corresponding
  `pytest` tests under a `tests/` directory and run `pytest`.
- If `training_data/` retraining is touched, note that results are
  stochastic (RL) — don't treat a single run's numbers as a regression
  baseline without multiple seeds.

## 4. Code Style
Follow the [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html):
- 2-space indentation inside docstring sections/continuations, 4-space
  indentation for code blocks; no tabs.
- Max line length 80 characters.
- Docstrings: triple-double-quoted, one-line summary ending in
  `.`/`?`/`!`, blank line, then `Args:` / `Returns:` / `Raises:` sections
  (Google style, not NumPy style) as shown in the guide.
- Type annotations encouraged for any new/modified public functions.
- Standard library imports, then third-party, then local — each group
  separated by a blank line; prefer absolute imports.
- Prefer small, focused functions; if a function exceeds ~40 lines, consider
  whether it should be split.
- For notebook cells: keep heavy logic in named functions/cells rather than
  long unstructured scripts, so review stays tractable.

## 5. Conventional Commits
All git commits must follow the [Conventional Commits v1.0.0](https://www.conventionalcommits.org/en/v1.0.0/#specification) specification.
- **Format:** `type(scope?): description`
- **Common Types:** `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `revert`

## 6. Conventional Comments
All code reviews, inline code comments (where applicable), and feedback must follow the [Conventional Comments](https://conventionalcomments.org/) standard.
- **Format:** `label [decorations]: subject`
- **Common Labels:** `praise`, `nit`, `suggestion`, `issue`, `chore`, `question`, `thought`

## 7. General Guidelines
- Validate changes against the notebook run and the bound-tightening
  invariant described in Section 3 before finishing a task.
- Keep commits granular and scoped to single logical changes.
- Don't commit large regenerated artifacts (e.g. retrained models, big CSVs)
  unless intentionally updating `models/` or `data/` as part of the task —
  check `.gitignore` first.
