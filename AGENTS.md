# Repository Guidelines

## Project Structure & Module Organization

This repository is organized as sports research workspaces. The active project is `nba-playoffs/`, an NBA playoff series prediction pipeline. Reusable Python code lives in `nba-playoffs/src/`: `data.py` for `nba_api` fetching and parquet caching, `features.py` for feature engineering, and `models.py` for training and evaluation helpers. Analysis notebooks live in `nba-playoffs/notebooks/` and run in numeric order. Generated data belongs in `nba-playoffs/data/raw/` or `nba-playoffs/data/processed/`; trained `.joblib` models belong in `nba-playoffs/models/`. These generated directories are gitignored.

## Build, Test, and Development Commands

Set up a local environment from the project root:

```bash
cd nba-playoffs
python3 -m venv .venv && source .venv/bin/activate
pip install nba_api pandas numpy scikit-learn xgboost shap matplotlib seaborn joblib tqdm pyarrow jupyterlab
jupyter lab
```

Run notebooks in order, starting with `notebooks/01-data-collection.ipynb`. Data collection uses cached parquet files after the first run. There is currently no packaged build step or committed test command.

## Coding Style & Naming Conventions

Use Python 3.10+ compatible code; Python 3.11 is preferred. Follow existing module style: 4-space indentation, type hints on public helpers, short docstrings, and uppercase constants such as `RAW_DIR`, `FEATURE_COLS`, and `TARGET_COL`. Prefer pandas and scikit-learn pipeline APIs. Avoid hardcoded absolute paths; derive paths from `Path(__file__).parents[...]`.

## Testing Guidelines

No formal test suite is present yet. When adding tests, use `pytest` and place them under `nba-playoffs/tests/` with names like `test_features.py` and `test_models.py`. Focus tests on deterministic helpers such as rest-day calculation, temporal train/test splitting, feature column expectations, and model metric formatting. Notebook validation means restarting the kernel and running the affected notebook top-to-bottom.

## Commit & Pull Request Guidelines

The git history uses conventional-style commits, for example `feat(06): extend to full bracket projection`, `fix(06): adjust stale proxy metrics`, and `docs(readme): add visuals`. Use `type(scope): summary`, where `type` is commonly `feat`, `fix`, or `docs`, and the scope can be a notebook number or project area.

Pull requests should include a concise description, changed notebooks or modules, verification performed, and any regenerated visuals. Do not commit raw/processed data, `.env` files, virtual environments, notebook checkpoints, or model artifacts unless the project explicitly changes that policy.

## Security & Configuration Tips

Use free/public data sources only unless a future change documents otherwise. Keep secrets in `.env` files, which are gitignored. Be considerate with `nba_api` calls: preserve the existing courtesy sleep and caching behavior to reduce rate-limit failures.
