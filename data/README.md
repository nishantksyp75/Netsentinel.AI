# CIC-IDS2017 data

NetSentinel uses labelled flow CSV files from CIC-IDS2017, not packet payloads. Download `MachineLearningCSV.zip` from the official Canadian Institute for Cybersecurity page: https://www.unb.ca/cic/datasets/ids-2017.html.

Extract all `*.csv` files beneath `data/raw/cicids2017/`. The training script finds CSVs recursively. This benchmark is large; start with `--sample-per-class` for development and use a consistent sample size when evaluating model performance.

The repository deliberately excludes raw data, processed matrices, IP addresses, local databases, and trained model artifacts.
