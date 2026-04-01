# upper-bound-unknotting

A self-contained repository for improving upper bounds on unknotting numbers with an RL-based reducer.

This version is set up to run **locally** and does **not** rely on Google Drive.

## Included files

This repository already contains:

- `data/unknotting.xlsx`
- `models/best_model.zip`
- `notebooks/upper_bound_unknotting_v6_local.ipynb`

So the notebook can be run directly after installing the dependencies.

## Repository layout

```text
upper-bound-unknotting/
├─ README.md
├─ requirements.txt
├─ .gitignore
├─ notebooks/
│  ├─ upper_bound_unknotting_v6_local.ipynb
│  └─ upper_bound_unknotting_v5_original.ipynb
├─ data/
│  └─ unknotting.xlsx
├─ models/
│  └─ best_model.zip
├─ training_data/                            # optional extra training files
│  ├─ hard_unknots.csv
│  ├─ very_hard_unknots.csv
│  └─ random_diagrams.csv
└─ outputs/
```

## What the notebook does

The notebook

1. loads `data/unknotting.xlsx`
2. fills missing Jones vectors from PD presentations when possible
3. finds unresolved unknotting-number ranges such as `[a,b]` with `a != b`
4. inflates the PD diagram
5. flips one crossing at a time
6. runs the RL unknotter / reducer
7. computes the Jones vector of the reduced knot
8. matches against the local workbook database, allowing mirrors
9. updates the upper bound while preserving the lower bound, for example `[2,3] -> [2,2]`
10. overwrites `data/unknotting.xlsx`

## Quick start

Create an environment and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Then launch Jupyter:

```bash
jupyter lab
```

and open:

```text
notebooks/upper_bound_unknotting_v6_local.ipynb
```

## Model behavior

The notebook first looks for a pretrained model in:

- `models/best_model.zip`
- `models/ppo_knot_rl_spherogram_continued.zip`
- `outputs/best_model.zip`

Since `models/best_model.zip` is already included here, it should run without retraining.

## Optional training data

If you want to retrain or continue training, you can additionally place files such as

- `training_data/hard_unknots.csv`
- `training_data/very_hard_unknots.csv`
- `training_data/random_diagrams.csv`

If no external training files are present, the notebook can fall back to PD data already stored inside `unknotting.xlsx`.

## Notes

- The notebook is designed to work from inside this repository.
- The main editable parameters are in the configuration cell near the top of the notebook.
- Results are written back into `data/unknotting.xlsx`.
