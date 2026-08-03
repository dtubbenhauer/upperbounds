"""Shared RL environment and PPO model-loading runtime."""

from __future__ import annotations

import ast
import csv
import json
import random
import re
from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import Any

import gymnasium as gym
import numpy as np
from gymnasium import spaces
from pydantic import BaseModel, Field
from spherogram import Link

from upperbounds.data.parsing import parse_pd_cell


_RE_DT_PREFIX = re.compile(r"^\s*DT\s*:\s*\[", re.I)
_RE_PDLIST = re.compile(
    r"^\s*\[\s*(\[\s*\d+(?:\s*,\s*\d+){3}\s*\]\s*,?\s*)+\]\s*$"
)
_RE_XPD = re.compile(r"[Xx]\s*\[")


class EnvCfg(BaseModel):
    """Configuration for the Spherogram knot-reduction environment."""

    max_steps: int = Field(default=500, ge=1)
    step_penalty: float = 0.05
    reward_finish: float = 10.0
    allow_backtrack: bool = True
    cap_max: int = Field(default=8, ge=0)
    w_delta: float = 1.0
    w_uphill: float = 0.5
    w_potential: float = 0.02
    seed: int = 0


def default_model_path_candidates(
    models_dir: Path,
    outputs_dir: Path,
) -> list[Path]:
    """Return the default model search order used by notebooks."""
    return [
        models_dir / "best_model.zip",
        models_dir / "ppo_knot_rl_spherogram_continued.zip",
        outputs_dir / "best_model.zip",
    ]


def default_local_training_files(
    training_dir: Path,
    data_dir: Path,
) -> list[Path]:
    """Return the default optional local training files."""
    return [
        training_dir / "hard_unknots.csv",
        training_dir / "very_hard_unknots.csv",
        training_dir / "random_diagrams.csv",
        training_dir / "random_diagrams.txt",
        data_dir / "hard_unknots.csv",
        data_dir / "very_hard_unknots.csv",
    ]


def find_existing_model_path(
    model_path_candidates: Sequence[Path | str],
) -> Path | None:
    """Return the first existing model path from candidate paths."""
    for path in model_path_candidates:
        candidate = Path(path)
        if candidate.exists():
            return candidate
    return None


def make_sb3_load_custom_objects(default_lr: float = 3e-4) -> dict[str, Any]:
    """Return fallback objects for loading older Stable-Baselines3 models."""
    learning_rate = float(default_lr)

    def _lr_schedule(_progress_remaining: float) -> float:
        return learning_rate

    return {
        "learning_rate": learning_rate,
        "lr_schedule": _lr_schedule,
    }


def parse_link_strict(source: str) -> Link:
    """Parse a PD/DT string into a Spherogram `Link`.

    Args:
        source: PD/DT string in one of the notebook-supported formats.

    Returns:
        Parsed Spherogram link.

    Raises:
        ValueError: If the source does not look like supported PD/DT input.
    """
    text = source.strip()
    if _RE_DT_PREFIX.match(text):
        return Link(text)
    if _RE_PDLIST.match(text):
        try:
            pd_obj = json.loads(text)
        except json.JSONDecodeError:
            pd_obj = ast.literal_eval(text)
        return Link(pd_obj)
    if _RE_XPD.search(text):
        try:
            return Link(text)
        except Exception:
            items = re.findall(r"[Xx]\s*\[([^\]]+)\]", text)
            if not items:
                raise
            blocks = []
            for item in items:
                numbers = [int(value.strip()) for value in item.split(",")]
                if len(numbers) != 4:
                    raise ValueError("PD block must have 4 integers")
                blocks.append(numbers)
            return Link(str(blocks))
    if (text.startswith("{") or text.startswith("[")) and not _RE_PDLIST.match(
        text
    ):
        try:
            obj = json.loads(text)
            if isinstance(obj, dict):
                for key in ("pd", "PD", "pd_code", "PD_code", "dt", "DT"):
                    if key in obj:
                        return parse_link_strict(obj[key])
        except Exception:
            pass
    raise ValueError("Not a PD/DT code")


def clean_pd_lines(
    lines: Iterable[str],
    max_keep: int | None = None,
) -> list[str]:
    """Filter strings down to parseable PD/DT lines."""
    good = []
    for source in lines:
        try:
            parse_link_strict(source)
            good.append(source.strip())
            if max_keep and len(good) >= max_keep:
                break
        except Exception:
            continue
    return good


def crossings(link: Link) -> int:
    """Return the number of crossings in a Spherogram link."""
    return len(link.crossings)


def is_trivial_zero(link: Link) -> bool:
    """Return whether a link has simplified to zero crossings."""
    return crossings(link) == 0


def riii_shuffle_only_link(
    link: Link,
    count: int,
    tries_per_move: int = 20,
) -> tuple[Link, int]:
    """Apply type-III Reidemeister shuffles without changing crossing count."""
    from spherogram.links import simplify as _simp

    list_fn = getattr(_simp, "possible_type_III_moves", None)
    apply_fn = getattr(_simp, "reidemeister_III", None)
    if list_fn is None or apply_fn is None:
        return link, 0

    current = link
    done = 0
    for _ in range(count):
        moves = list_fn(current)
        if not moves:
            break
        tries = min(tries_per_move, len(moves))
        before_crossings = crossings(current)
        success = False
        for triangle in random.sample(moves, tries):
            apply_fn(current, triangle)
            if crossings(current) == before_crossings:
                success = True
                break
        if not success:
            break
        done += 1
    return current, done


def read_first_col_local(
    path: str,
    has_header: bool = True,
    encoding: str = "utf-8",
) -> list[str]:
    """Read the first CSV column from a local training-data file."""
    output = []
    with open(path, "r", encoding=encoding, newline="") as input_file:
        reader = csv.reader(input_file)
        if has_header:
            next(reader, None)
        for row in reader:
            if row:
                output.append(row[0].strip())
    return output


def workbook_pd_lines(
    df: Any,
    pd_col: str,
    max_keep: int | None = None,
) -> list[str]:
    """Extract parseable PD lines from a workbook DataFrame."""
    raw = []
    for _, row in df.iterrows():
        pd_list = parse_pd_cell(row.get(pd_col))
        if pd_list is not None:
            raw.append(json.dumps(pd_list))
            if max_keep is not None and len(raw) >= max_keep:
                break
    return raw


class SphKnotEnv(gym.Env):
    """Spherogram knot-reduction environment used by PPO."""

    def __init__(self, pd_lines: list[str], cfg: EnvCfg):
        """Initialize the environment."""
        super().__init__()
        self.cfg = cfg
        self.pd_lines = pd_lines
        self.rng = random.Random(cfg.seed)
        self.num_actions = 4 if self.cfg.allow_backtrack else 3
        self.action_space = spaces.MultiDiscrete(
            np.array(
                [self.num_actions, self.cfg.cap_max + 1],
                dtype=np.int64,
            )
        )
        self.obs_dim = 6
        self.observation_space = spaces.Box(
            low=-np.inf,
            high=np.inf,
            shape=(self.obs_dim,),
            dtype=np.float32,
        )
        self.L = None
        self._steps = 0
        self._last_drop = 0
        self._after_backtrack = False
        self._blocked = [False, False, False, False]

    def _reset_blocks(self) -> None:
        self._blocked = [False, False, False, False]

    def _map_blocked_mode(self, mode: int) -> int:
        mapped_mode = mode % self.num_actions
        for _ in range(self.num_actions):
            if not self._blocked[mapped_mode]:
                return mapped_mode
            mapped_mode = (mapped_mode + 1) % self.num_actions
        return min(3, self.num_actions - 1)

    def _obs(self) -> np.ndarray:
        crossing_count = crossings(self.L)
        try:
            components = len(self.L.link_components)
        except Exception:
            components = 1
        tmp = Link(self.L.PD_code())
        try:
            reduced = tmp.simplify(mode="basic")
        except TypeError:
            reduced = tmp.simplify()
        can_reduce = (
            1.0 if (reduced and crossings(tmp) < crossing_count) else 0.0
        )
        recent = 1.0 if getattr(self, "_last_drop", 0) > 0 else 0.0
        return np.array(
            [crossing_count, components, self._steps, can_reduce, recent, 1.0],
            dtype=np.float32,
        )

    def reset(self, *, seed=None, options=None):
        """Reset the environment to a random PD line."""
        super().reset(seed=seed)
        self._steps = 0
        self._last_drop = 0
        self._after_backtrack = False
        self._reset_blocks()
        for _ in range(10):
            source = self.rng.choice(self.pd_lines)
            try:
                self.L = parse_link_strict(source)
                break
            except Exception:
                self.L = None
        if self.L is None:
            self.L = parse_link_strict(self.pd_lines[0])
        return self._obs(), {"crossings": crossings(self.L)}

    def step(self, action):
        """Run one reduction action."""
        self._steps += 1
        if isinstance(action, (list, tuple, np.ndarray)):
            mode_requested, cap = int(action[0]), int(action[1])
        else:
            mode_requested, cap = int(action), 0
        cap = max(0, min(cap, self.cfg.cap_max))
        mode = self._map_blocked_mode(mode_requested)

        crossings_before = crossings(self.L)
        if mode == 0:
            try:
                self.L.simplify(mode="basic")
            except TypeError:
                self.L.simplify()
        elif mode == 1:
            steps = cap if cap > 0 else 1
            self.L.simplify(mode="level", type_III_limit=steps)
        elif mode == 2:
            steps = cap if cap > 0 else 1
            self.L.simplify(mode="pickup", type_III_limit=steps)
        elif mode == 3 and self.num_actions == 4:
            steps = cap if cap > 0 else 1
            self.L.backtrack(
                steps=steps,
                prob_type_1=0.35,
                prob_type_2=0.65,
            )
            self.L, _ = riii_shuffle_only_link(self.L, min(steps, 2))

        crossings_after = crossings(self.L)
        delta = crossings_before - crossings_after
        self._last_drop = max(delta, 0)

        reward = (
            self.cfg.w_delta * delta
            - self.cfg.w_uphill * max(0, -delta)
            - self.cfg.w_potential * crossings_after
            - self.cfg.step_penalty
        )

        done = False
        if is_trivial_zero(self.L):
            reward += self.cfg.reward_finish
            done = True
        if self._steps >= self.cfg.max_steps:
            done = True

        if delta > 0:
            self._reset_blocks()
        elif mode == 3:
            self._reset_blocks()
        elif delta < 0:
            self._blocked[mode] = True

        self._after_backtrack = mode == 3 and self.num_actions == 4

        info = {
            "crossings": crossings_after,
            "delta": delta,
            "mode_requested": mode_requested,
            "mode_effective": mode,
            "cap": cap,
            "blocked": tuple(self._blocked),
        }
        return self._obs(), reward, done, False, info


def load_training_pd_lines(
    local_extra_files: Sequence[Path],
    df: Any,
    pd_col: str,
    seed: int,
) -> list[str]:
    """Load and clean local or workbook-sourced training PD lines."""
    raw = []

    for path in local_extra_files:
        if path.exists():
            try:
                extra = read_first_col_local(str(path), has_header=True)
                raw += extra
                print(f"Loaded local extra {path.name}: {len(extra)}")
            except Exception as exc:
                print(f"Could not load {path.name}: {exc}")

    if not raw:
        raw = workbook_pd_lines(df, pd_col)
        print(f"Falling back to workbook PD data: {len(raw)} examples")

    pd_lines = clean_pd_lines(raw, max_keep=None)
    random.Random(seed).shuffle(pd_lines)
    if not pd_lines:
        raise RuntimeError(
            "No valid PD/DT strings available for training. "
            "Add local CSV/TXT files under training_data/ or ensure "
            "unknotting.xlsx contains PD data."
        )
    return pd_lines


def make_single_env(pd_list: list[list[int]], cfg: EnvCfg):
    """Create a Stable-Baselines3 vector environment for one PD."""
    from stable_baselines3.common.vec_env import DummyVecEnv

    pd_string = json.dumps(pd_list)
    pd_lines_single = [pd_string]

    def _make():
        return SphKnotEnv(pd_lines_single, cfg)

    return DummyVecEnv([_make])


def run_unknotter_on_pd(
    pd_list: list[list[int]],
    model: Any,
    cfg: EnvCfg,
    episodes: int = 3,
    return_best_pd: bool = False,
):
    """Run a trained unknotter model against a planar diagram."""
    vec_env = make_single_env(pd_list, cfg)
    success = False
    best_crossings_global = len(pd_list)
    best_pd_global = [list(quad) for quad in pd_list]

    for _ in range(episodes):
        obs = vec_env.reset()
        best_crossings_ep = best_crossings_global
        best_pd_ep = best_pd_global

        for _step in range(cfg.max_steps):
            action, _ = model.predict(obs, deterministic=True)
            obs, _rewards, dones, infos = vec_env.step(action)
            info = infos[0]
            current_crossings = info.get("crossings", None)
            try:
                current_pd = [
                    list(quad) for quad in vec_env.envs[0].L.PD_code()
                ]
            except Exception:
                current_pd = None

            if (
                current_crossings is not None
                and current_crossings < best_crossings_ep
                and current_pd is not None
            ):
                best_crossings_ep = current_crossings
                best_pd_ep = current_pd

            if current_crossings == 0:
                success = True
                if current_pd is not None:
                    best_crossings_ep = 0
                    best_pd_ep = current_pd
                break
            if dones[0]:
                break

        if best_crossings_ep < best_crossings_global:
            best_crossings_global = best_crossings_ep
            best_pd_global = best_pd_ep
        if success:
            break

    vec_env.close()
    if return_best_pd:
        return success, best_crossings_global, best_pd_global
    return success, best_crossings_global


def load_or_train_ppo_model(
    model_path_candidates: Sequence[Path],
    train_if_model_missing: bool,
    train_steps_if_needed: int,
    cfg: EnvCfg,
    local_extra_files: Sequence[Path],
    df: Any,
    pd_col: str,
    seed: int,
    output_model_path: Path,
):
    """Load an existing PPO model or train a fresh fallback model."""
    from stable_baselines3 import PPO
    from stable_baselines3.common.vec_env import DummyVecEnv

    best_model_path = find_existing_model_path(model_path_candidates)
    if best_model_path is not None:
        custom_objects = make_sb3_load_custom_objects()
        model = PPO.load(
            str(best_model_path),
            device="auto",
            custom_objects=custom_objects,
        )
        print("Loaded existing model:", best_model_path)
        return model, best_model_path

    if not train_if_model_missing:
        raise FileNotFoundError(
            "No trained model found in MODEL_PATH_CANDIDATES, "
            "and TRAIN_IF_MODEL_MISSING=False."
        )

    print("No existing model found. Training a fresh one.")
    print("Searched these locations:")
    for path in model_path_candidates:
        print("  -", path)

    pd_lines_train = load_training_pd_lines(local_extra_files, df, pd_col, seed)
    vec_env = DummyVecEnv([lambda: SphKnotEnv(pd_lines_train, cfg)])
    model = PPO(
        "MlpPolicy",
        vec_env,
        learning_rate=3e-4,
        n_steps=2048,
        batch_size=256,
        n_epochs=10,
        gamma=0.995,
        gae_lambda=0.97,
        clip_range=0.2,
        ent_coef=0.01,
        vf_coef=0.5,
        max_grad_norm=0.5,
        seed=seed,
        verbose=1,
    )
    model.learn(total_timesteps=train_steps_if_needed, progress_bar=True)
    model.save(str(output_model_path))
    vec_env.close()
    print("Saved trained model to:", output_model_path)
    return model, output_model_path
