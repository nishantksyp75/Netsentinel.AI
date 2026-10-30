from __future__ import annotations

from pathlib import Path
import re
import numpy as np
import pandas as pd

LABEL = "Label"

def canonical(name: str) -> str:
    return re.sub(r"\s+", " ", name.replace("\ufeff", "").strip())

def load_cicids(directory: str | Path, sample_per_class: int | None = None, seed: int = 42) -> pd.DataFrame:
    files = sorted(Path(directory).rglob("*.csv"))
    if not files:
        raise FileNotFoundError(f"No CSV files beneath {directory}. See data/README.md.")
    frames = []
    for file in files:
        frame = pd.read_csv(file, low_memory=False)
        frame.columns = [canonical(c) for c in frame.columns]
        if LABEL not in frame.columns:
            raise ValueError(f"{file.name} has no '{LABEL}' column")
        frame[LABEL] = frame[LABEL].astype(str).str.strip()
        frame["__source_file"] = file.name
        frames.append(frame)
    data = pd.concat(frames, ignore_index=True, sort=False)
    data = data.replace([np.inf, -np.inf], np.nan).drop_duplicates().dropna(subset=[LABEL])
    if sample_per_class:
        data = (data.groupby(LABEL, group_keys=False)
                .apply(lambda x: x.sample(min(len(x), sample_per_class), random_state=seed), include_groups=True))
    return data.reset_index(drop=True)

def numeric_features(data: pd.DataFrame) -> list[str]:
    excluded = {LABEL, "Flow ID", "Source IP", "Destination IP", "Timestamp", "SimillarHTTP", "Inbound"}
    features = [c for c in data.columns if c not in excluded and not c.startswith("__")]
    converted = data[features].apply(pd.to_numeric, errors="coerce")
    return [c for c in converted if converted[c].notna().any()]

def inventory(data: pd.DataFrame) -> dict:
    return {"rows": int(len(data)), "columns": int(len(data.columns)), "duplicates_removed_before_load": None,
            "missing_cells": int(data.isna().sum().sum()), "class_distribution": data[LABEL].value_counts().to_dict()}
