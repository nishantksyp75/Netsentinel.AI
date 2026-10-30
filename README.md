# NetSentinel AI

**NetSentinel AI** is an offline-first network intrusion detection and incident investigation application. It combines supervised machine learning, anomaly detection, risk scoring, security-knowledge retrieval, and analyst-controlled incident decisions.

The project is designed as a defensive security workflow: it identifies suspicious network flows, records evidence, supports investigation, and keeps consequential decisions under human control.

## Key capabilities

- **Network-flow detection:** train Random Forest, XGBoost, and Isolation Forest models on CIC-IDS2017 flow records.
- **Hybrid risk scoring:** combine supervised attack probability, anomaly signals, and available evidence.
- **Feature evidence:** expose model-related feature evidence with alert records.
- **Alert management:** persist and review generated alerts.
- **Investigation workflow:** retrieve related alerts and relevant defensive security guidance.
- **Human approval:** record analyst approval or rejection with an audit trail.
- **REST API:** FastAPI endpoints with API-key authentication support and optional rate limiting.
- **Analyst dashboard:** Streamlit interface for alerts, investigations, and controlled AI-assisted workflows.
- **Persistence:** SQLite by default, with optional PostgreSQL configuration.

## Architecture

```text
CIC-IDS2017 flow CSVs
        |
        v
Data loading and preprocessing
        |
        v
Model training
(Random Forest / XGBoost / Isolation Forest)
        |
        v
Trained model bundle
        |
        v
FastAPI scoring API
        |
        v
Risk score + feature evidence
        |
        v
Alert and investigation workflow
        |
        +------> Defensive knowledge retrieval
        |
        v
Analyst review and decision
        |
        v
Persisted audit record

Streamlit dashboard <----> FastAPI
```

## Technology stack

| Area | Technology |
|---|---|
| Language | Python |
| Machine learning | scikit-learn, XGBoost |
| Data processing | pandas, NumPy |
| API | FastAPI, Uvicorn |
| Dashboard | Streamlit |
| Persistence | SQLAlchemy, SQLite |
| Knowledge retrieval | TF-IDF, cosine similarity |
| Containerization | Docker, Docker Compose |
| Testing | pytest |

## Requirements

- Python 3.11 or newer
- Git
- CIC-IDS2017 flow CSV files for model training
- Docker Desktop (optional, for containerized execution)

## Setup

Clone the repository and enter the project directory:

```powershell
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd NetSentinel.AI
```

Create and activate a virtual environment:

```powershell
py -3.12 -m venv .venv312
.\.venv312\Scripts\Activate.ps1
```

Install dependencies:

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If PowerShell blocks environment activation, run the Python executable directly using `.venv312\Scripts\python.exe`.

## Prepare the dataset

Download CIC-IDS2017 from the Canadian Institute for Cybersecurity:

https://www.unb.ca/cic/datasets/ids-2017.html

Extract the flow CSV files beneath:

```text
data/raw/cicids2017/
```

The dataset is not included in this repository.

## Train the detection models

Run training from the project root:

```powershell
python scripts/train.py --data-dir data/raw/cicids2017 --sample-per-class 20000
```

The training process creates:

- `models/detectors.joblib` — trained model bundle
- `models/metrics.json` — training and evaluation metrics
- `models/dataset_inventory.json` — dataset inventory

These generated artifacts are intentionally excluded from version control. Training may require substantial memory and processing time depending on the dataset and sample size.

The training script also supports `--seed`, `--output-dir`, and the split strategies `stratified_random`, `chronological`, and `source_file_holdout`.

## Run locally

After training, start the API:

```powershell
python -m uvicorn app.api.main:app --host 127.0.0.1 --port 8000
```

In a second terminal, activate the same environment and start the dashboard:

```powershell
python -m streamlit run app/dashboard/Home.py
```

Open:

- Dashboard: http://localhost:8501
- API documentation: http://127.0.0.1:8000/docs
- API health: http://127.0.0.1:8000/health

Alternatively, on Windows PowerShell, use the combined launcher:

```powershell
.\run_netsentinel.ps1
```

The launcher supports `.venv312` and `.venv` environments.

## Docker

Train the model locally first so that `models/detectors.joblib` exists. Then run:

```powershell
docker compose up --build
```

Open:

- Dashboard: http://localhost:8501
- API documentation: http://localhost:8000/docs

Docker Compose mounts the local `models` and `data` directories into the API container. The trained model remains local and is not copied into the Git repository.

## Configuration

Copy `.env.example` to `.env` and configure the values required by your environment.

Important settings include:

- `NETSENTINEL_API_KEY` — optional API authentication key
- `NETSENTINEL_RATE_LIMIT_PER_MINUTE` — optional request rate limit
- `DATABASE_URL` — database connection
- `MODEL_DIR` — trained model directory
- `KNOWLEDGE_DIR` — local defensive knowledge directory

Never commit `.env`, credentials, private datasets, or local database files.

## Tests

Run the test suite:

```powershell
python -m pytest -q
```

## Security boundaries

NetSentinel AI is a defensive analysis prototype. Its investigation workflow retrieves stored evidence and security guidance; it does not independently block traffic, modify network configurations, or execute containment actions. Consequential actions remain subject to analyst review and authorization.

## Repository hygiene

The repository intentionally excludes:

- Raw and processed datasets
- Trained model binaries and generated metrics
- Local databases and backups
- Environment files, credentials, and secrets
- Private documents and generated reports
- Python virtual environments and temporary files
