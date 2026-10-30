import numpy as np
import pandas as pd

from app.detection.splits import three_way_indices


def test_chronological_split_orders_rows_by_timestamp():
    data = pd.DataFrame({"Timestamp": ["03/07/2017 10:00", "03/07/2017 08:00", "03/07/2017 09:00", "03/07/2017 11:00", "03/07/2017 12:00"] * 5})
    labels = np.array([0, 1, 0, 1, 0] * 5)
    train, validation, test = three_way_indices(data, labels, "chronological", seed=42)
    assert len(train) == 15 and len(validation) == 5 and len(test) == 5
    assert set(train).isdisjoint(validation)
    assert set(validation).isdisjoint(test)
    assert set(test) == {4, 9, 14, 19, 24}


def test_stratified_random_split_covers_every_row_once():
    data = pd.DataFrame({"Timestamp": ["03/07/2017 10:00"] * 50})
    labels = np.array([0, 1] * 25)
    train, validation, test = three_way_indices(data, labels, "stratified_random", seed=42)
    assert len(train) == 30 and len(validation) == 10 and len(test) == 10
    assert set(train) | set(validation) | set(test) == set(range(50))


def test_source_file_holdout_keeps_files_separate():
    data = pd.DataFrame({"__source_file": [f"capture_{index}.csv" for index in range(5) for _ in range(4)]})
    labels = np.array([0, 1, 0, 1] * 5)
    train, validation, test = three_way_indices(data, labels, "source_file_holdout", seed=42)
    assert set(data.iloc[train]["__source_file"]).isdisjoint(data.iloc[test]["__source_file"])
    assert len(train) + len(validation) + len(test) == len(data)
