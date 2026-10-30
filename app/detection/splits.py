"""Reproducible train, validation, and test split strategies."""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split


def three_way_indices(data: pd.DataFrame, labels: np.ndarray, strategy: str, seed: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return 60/20/20 positional indices without fitting on validation or test rows."""
    positions = np.arange(len(data))
    if strategy == "stratified_random":
        train_validation, test = train_test_split(
            positions, test_size=0.2, random_state=seed, stratify=labels
        )
        train, validation = train_test_split(
            train_validation,
            test_size=0.25,
            random_state=seed,
            stratify=labels[train_validation],
        )
        return np.asarray(train), np.asarray(validation), np.asarray(test)

    if strategy == "chronological":
        if "Timestamp" not in data.columns:
            raise ValueError("Chronological evaluation requires a Timestamp column.")
        timestamps = pd.to_datetime(data["Timestamp"], errors="coerce", dayfirst=True)
        valid_fraction = float(timestamps.notna().mean())
        if valid_fraction < 0.95:
            raise ValueError(f"Only {valid_fraction:.1%} of timestamps parsed; chronological split is unsafe.")
        ordered = np.argsort(timestamps.to_numpy(), kind="stable")
        train_end = int(len(ordered) * 0.60)
        validation_end = int(len(ordered) * 0.80)
        return ordered[:train_end], ordered[train_end:validation_end], ordered[validation_end:]

    if strategy == "source_file_holdout":
        if "__source_file" not in data.columns:
            raise ValueError("Source-file holdout requires loader provenance metadata.")
        sources = sorted(data["__source_file"].dropna().unique().tolist())
        if len(sources) < 5:
            raise ValueError("Source-file holdout requires at least five input CSV files.")
        train_end = max(1, int(len(sources) * 0.60))
        validation_end = max(train_end + 1, int(len(sources) * 0.80))
        train_sources, validation_sources, test_sources = sources[:train_end], sources[train_end:validation_end], sources[validation_end:]
        return (
            np.flatnonzero(data["__source_file"].isin(train_sources)),
            np.flatnonzero(data["__source_file"].isin(validation_sources)),
            np.flatnonzero(data["__source_file"].isin(test_sources)),
        )

    raise ValueError("strategy must be 'stratified_random', 'chronological', or 'source_file_holdout'")
