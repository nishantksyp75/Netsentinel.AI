# Final demonstration checklist

1. Start the backend and dashboard using the README or `run_netsentinel.ps1`.
2. Show the dashboard overview and existing alerts.
3. Submit one redacted, schema-compatible benchmark flow to `POST /score`.
4. On Alerts, show prediction, probabilities, risk score, anomaly signal, and model evidence.
5. Start the controlled investigation. Show its evidence trace and retrieved defensive sources.
6. Approve or reject the recommendation and show the persisted status.
7. Explain the safety boundary: model detection, RAG context, and agent orchestration do not perform network changes; the analyst owns consequential decisions.

Before the demonstration, run `python -m pytest -q`, verify API and dashboard connectivity, and confirm that local secrets, datasets, databases, and generated model artifacts are excluded from version control.
