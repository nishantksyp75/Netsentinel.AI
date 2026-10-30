from __future__ import annotations
import argparse, json, sys
from pathlib import Path

# Allow `python scripts/train.py` from any working directory.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
from app.detection.data import inventory, load_cicids
from app.detection.train import train_models

p=argparse.ArgumentParser(description="Train reproducible NetSentinel models on real CIC-IDS2017 CSVs")
p.add_argument("--data-dir",required=True); p.add_argument("--output-dir",default="models"); p.add_argument("--sample-per-class",type=int); p.add_argument("--seed",type=int,default=42)
p.add_argument("--split-strategy", choices=["stratified_random", "chronological", "source_file_holdout"], default="stratified_random", help="Use chronological only when timestamps exist. Source-file holdout is a separate robustness experiment and may contain classes absent from training.")
args=p.parse_args(); data=load_cicids(args.data_dir,args.sample_per_class,args.seed)
Path(args.output_dir).mkdir(parents=True,exist_ok=True)
Path(args.output_dir,"dataset_inventory.json").write_text(json.dumps(inventory(data),indent=2),encoding="utf-8")
metrics=train_models(data,args.output_dir,args.seed,args.split_strategy)
print(json.dumps(metrics,indent=2))
