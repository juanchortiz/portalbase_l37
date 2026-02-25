# AGENTS.md

## Cursor Cloud specific instructions

### Overview

Portal Base is a Python/Streamlit app for browsing Portuguese public procurement data from Base.gov.pt. Single-service, no Docker or database server required (uses embedded SQLite).

### Running the app

```bash
streamlit run app.py --server.headless true --server.port 8501 --browser.gatherUsageStats false
```

The `FAST_BOOT` env var defaults to `"1"`, which skips heavy startup work. Set `FAST_BOOT=0` to disable.

### Required secrets

- `BASE_API_KEY` — needed for all data functionality. Without it the app starts but shows an initialization error and stops rendering.
- `HUBSPOT_API_TOKEN` — optional, only for CRM deal creation features.

### Caveats

- `~/.local/bin` must be on `PATH` for the `streamlit` CLI (pip installs there as non-root).
- No linter, formatter, or test framework is configured in this repo. Test files are gitignored (`test_*.py`).
- See `README.md` for CLI scripts and API usage examples.
