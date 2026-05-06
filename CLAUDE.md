<!-- GSD:project-start source:PROJECT.md -->
## Project

**Sports ML Research**

A multi-sport machine learning research repository organized by league (NFL, NBA, MLB). Each sport has its own folder with Jupyter notebooks for exploration and Python scripts for repeatable model runs. The goal is pure research — understanding what drives player performance.

**Core Value:** Each sport folder is a self-contained research workspace where any analysis can be run top-to-bottom.

### Constraints

- **Stack**: Python 3.10+, pandas, scikit-learn, statsmodels, Jupyter notebooks
- **Data**: Free/public sources only for now
- **Style**: Notebooks run top-to-bottom; config cells first; no hardcoded paths
<!-- GSD:project-end -->

<!-- GSD:stack-start source:research/STACK.md -->
## Technology Stack

## Recommended Stack
### Core Technologies
| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Python | 3.11 | Runtime | 3.11 is the sweet spot for 2025: faster than 3.10, fully supported by every library here, and 3.12/3.13 still have occasional dependency lags in the data science ecosystem. 3.10 is the floor per project constraints. |
| pandas | 2.2.x | Tabular data manipulation | v2.x brought copy-on-write semantics (default in 2.2) that eliminate silent mutation bugs common in research notebooks. The entire sports data ecosystem returns DataFrames. |
| numpy | 1.26.x / 2.0.x | Array math | numpy 2.0 (released mid-2024) tightened dtype semantics; wait for 2.0 only if all deps (pandas, scikit-learn) have confirmed support. 1.26 is safe universal baseline. |
| scikit-learn | 1.5.x | Classical ML: regression, cross-validation, pipelines | The right tool for this project's stated work (combine metrics → performance regression). Pipelines + GridSearchCV are the correct pattern for repeatable model runs. Not PyTorch — this is structured tabular data, not deep learning. |
| statsmodels | 0.14.x | Statistical regression, hypothesis testing, OLS diagnostics | Required alongside scikit-learn for this domain. scikit-learn doesn't expose p-values, confidence intervals, or heteroskedasticity tests. For "what drives career performance" questions you need OLS summary tables, VIF, Breusch-Pagan — statsmodels delivers all of these. |
| jupyter | >=1.0 (via JupyterLab 4.x) | Interactive EDA notebooks | JupyterLab 4 is the current standard. Use `jupyterlab` not `jupyter notebook` (classic) — better extension support, variable inspector, diffable outputs. |
| matplotlib | 3.9.x | Base plotting | Required by seaborn and many scikit-learn plot utilities. Keep pinned; seaborn versions bind tightly to matplotlib. |
| seaborn | 0.13.x | Statistical visualization | v0.13 rewrote the objects API — use `sns.objects` for faceted plots in EDA. Scatter matrices, distribution plots, residual plots are one-liners. |
### Data Acquisition — Sport-Specific
| Library | Version | Sport | Purpose | Why |
|---------|---------|-------|---------|-----|
| nfl-data-py | 0.3.x | NFL | Play-by-play, player stats, combine data, rosters | The canonical Python wrapper around nflverse (the R ecosystem's data). Returns clean DataFrames. Combine data is in `import_combine_data()`. Actively maintained as of 2024. |
| nba_api | 1.4.x | NBA | All NBA.com endpoints: player stats, shot charts, advanced box scores | Official-ish; scrapes stats.nba.com. Covers everything from per-game to play-by-play. Rate-limit aware — add sleep between calls. |
| pybaseball | 2.2.x | MLB | FanGraphs, Baseball Reference, Statcast (via Baseball Savant) | Best-in-class for MLB research. `statcast()`, `batting_stats()`, `pitching_stats()` are the workhorses. Caches locally by default. |
### Supporting Libraries
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| xgboost | 2.0.x | Gradient boosted trees | When OLS assumptions are violated (non-linearity, interaction effects) or when you want a predictive model alongside the explanatory regression. Add in a later phase — don't start here. |
| lightgbm | 4.3.x | Faster gradient boosted trees | Alternative to XGBoost for larger datasets (Statcast play-by-play can be millions of rows). Same interface, faster training. Pick one; don't use both. |
| shap | 0.45.x | Model explainability | Essential for interpreting tree models in research context. Use after any XGBoost/LightGBM model to answer "which features matter." |
| scipy | 1.13.x | Statistical tests, distributions | Needed for correlation tests (Spearman, Pearson with CI), normality checks. statsmodels depends on it; include explicitly. |
| plotly | 5.x | Interactive charts | Optional but valuable in notebooks for exploratory scatter plots where you want hover. Don't use for final paper-quality figures — matplotlib/seaborn for those. |
| requests / httpx | requests 2.32.x | HTTP for manual API calls | nba_api and some custom data fetches need this. httpx if you ever want async; requests otherwise. |
| python-dotenv | 1.0.x | Environment variable management | For any API keys (Odds API is out of scope, but pattern is correct for any future keys). |
| tqdm | 4.x | Progress bars | Essential for loops over seasons/players in data collection scripts. |
| pytest | 8.x | Testing | Test data loading utilities and model helper scripts. Not needed for notebooks. |
| ruff | 0.4.x | Linting + formatting | Per project style conventions. Replaces flake8 + black + isort in one tool. |
### Development Tools
| Tool | Purpose | Notes |
|------|---------|-------|
| JupyterLab 4.x | Primary notebook environment | `pip install jupyterlab`. Extensions: `jupyterlab-git` for diff visibility. |
| uv | Fast venv + dependency management | `pip install uv` then `uv venv` + `uv pip install`. 10-100x faster than pip for resolving. Use as the venv/install tool even though pip syntax is preserved. Not a replacement for requirements.txt — still pin with that. |
| nbstripout | Notebook output stripping for git | `nbstripout --install` registers a git filter that strips cell outputs before commit. Critical for a research repo — raw notebook outputs bloat git history and create messy diffs. |
| pre-commit | Git hook runner | Runs ruff + nbstripout automatically on commit. One `pre-commit install` call sets up the project. |
## Installation
# Create venv (top-level shared, per PROJECT.md)
# Core data + ML
# Sport-specific data
# Visualization
# Notebook
# ML extras (add when needed, not day 1)
# pip install xgboost==2.0.* lightgbm==4.3.* shap==0.45.*
# Dev / tooling
## Alternatives Considered
| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| nfl-data-py | nflreadr (R) | If the team is R-native — nflreadr is the primary source, nfl-data-py mirrors it. Python project → nfl-data-py. |
| nfl-data-py | sportradar / ESPN API | If you need licensed real-time data. Free tier doesn't cover historical combine data well. |
| nba_api | basketball-reference-scraper | If nba_api rate-limits become painful. basketball-reference-scraper is slower but Basketball Reference has cleaner historical data in some cases. |
| pybaseball | baseball-reference-scraper | pybaseball is more comprehensive (Statcast) and better maintained. basketball-reference-scraper is backup. |
| scikit-learn + statsmodels | PyTorch / TensorFlow | Only if you move to sequence modeling (career trajectory over time) or image-based scouting. Not appropriate for tabular regression. |
| seaborn 0.13 objects API | altair | Altair is excellent for grammar-of-graphics style plots but adds a dependency with a steeper learning curve. Seaborn is sufficient for EDA. |
| JupyterLab | VS Code Jupyter extension | Both work. JupyterLab is better for pure notebook workflows; VS Code better if you split time between .py scripts and notebooks. Either is fine — don't mix within the project. |
| uv | conda / mamba | Conda is better for managing non-Python system dependencies (e.g., CUDA). This project has none. uv is faster for pure Python envs. |
| nbstripout | manual git attributes | nbstripout automates what you'd otherwise forget. Always use it. |
## What NOT to Use
| Avoid | Why | Use Instead |
|-------|-----|-------------|
| `sportsreference` (sportsipy) | Unmaintained since ~2022, scrapes pages that have changed structure, frequent breakage reported | nfl-data-py, nba_api, pybaseball per sport |
| `nflscrapR` (Python port attempts) | nflscrapR is an R package; Python ports are unofficial forks with no maintenance guarantees | nfl-data-py (officially mirrors nflverse) |
| Raw ESPN undocumented API calls | No official support, endpoints change without notice, fragile | nba_api (wraps stats.nba.com more reliably) |
| Jupyter Notebook (classic) | `jupyter notebook` is the legacy interface; no longer actively developed | JupyterLab 4 |
| `pickle` for model persistence | Pickle is version-sensitive and a security risk; models pickled against one sklearn version break on another | `joblib` (ships with scikit-learn) or `skops` for safe sklearn serialization |
| `%matplotlib inline` magic | Deprecated in modern JupyterLab; outputs render by default | Remove the magic; use `plt.show()` or just return fig objects |
| Global pip installs | Pollutes system Python; version conflicts across projects | Always work inside `.venv` |
| pandas `inplace=True` | With pandas 2.x copy-on-write, inplace semantics are confusing and will be removed in 3.0 | Always assign: `df = df.method()` |
## Stack Patterns by Variant
- Load data with nfl-data-py, wrangle with pandas
- Visualize distributions with seaborn, correlations with `df.corr()` + heatmap
- OLS with statsmodels (`smf.ols("career_av ~ forty_time + vertical + C(position)", data=df).fit()`)
- Keep notebooks self-contained: data load → clean → EDA → model → interpretation, top to bottom
- Use scikit-learn Pipelines: `Pipeline([('scaler', StandardScaler()), ('model', Ridge())])`
- Serialize with joblib: `joblib.dump(pipeline, 'models/combine_regression.joblib')`
- Accept CLI args with argparse or click for season/position parameters
- Log metrics to stdout (no MLflow needed at this scale)
- XGBoost with `early_stopping_rounds` to avoid overfitting on small sports datasets
- SHAP for feature importance — don't rely on `.feature_importances_` alone
- Cross-validate by season (temporal splits), not random splits, to avoid leakage
- Add polars as a faster DataFrame library for the heavy lifting, keep pandas for model input prep
- LightGBM over XGBoost for speed
- Consider DuckDB for in-process SQL queries over parquet files
## Version Compatibility
| Package | Compatible With | Notes |
|---------|-----------------|-------|
| pandas 2.2.x | numpy 1.26.x | numpy 2.0 is compatible with pandas 2.2.2+ but 1.26 is safer for initial setup |
| scikit-learn 1.5.x | numpy 1.26.x, scipy 1.13.x | No known issues |
| statsmodels 0.14.x | pandas 2.2.x, numpy 1.26.x | Confirmed compatible |
| seaborn 0.13.x | matplotlib 3.8.x–3.9.x | seaborn 0.13 requires matplotlib >= 3.3; 3.9 is the current release |
| nba_api 1.4.x | requests 2.x | nba_api pins requests internally; don't override |
| pybaseball 2.2.x | pandas 2.x | 2.x compatibility was added in pybaseball 2.2; earlier versions have dtype issues with pandas 2 |
| xgboost 2.0.x | scikit-learn 1.5.x | xgboost 2.0 uses sklearn 1.x estimator API; compatible |
| shap 0.45.x | xgboost 2.0.x, lightgbm 4.x | shap TreeExplainer works with both |
## Confidence Notes
| Area | Confidence | Notes |
|------|------------|-------|
| Core data science stack (pandas, scikit-learn, statsmodels, seaborn) | HIGH | Extremely stable, well-documented, confirmed pattern for tabular ML research |
| nfl-data-py | MEDIUM | Actively maintained as of Aug 2025 training data; verify current version on PyPI before install |
| nba_api | MEDIUM | Has had rate-limit changes in the past; verify 1.4.x is current on PyPI |
| pybaseball | MEDIUM | 2.2.x claimed; verify on PyPI — project has had sporadic maintenance |
| xgboost/lightgbm versions | MEDIUM | Version numbers from training data; check PyPI before pinning |
| uv as install tool | HIGH | uv is the clear 2025 standard for fast Python env management |
| nbstripout recommendation | HIGH | Universal consensus in data science teams using git |
## Sources
- Training data (knowledge cutoff Aug 2025) — all library facts; MEDIUM confidence
- PyPI JSON API (blocked in this run) — versions unverified externally; pin after manual `pip index versions <package>` check
- nflverse documentation (https://nflverse.nflverse.com/) — nfl-data-py is the Python mirror
- nba_api GitHub (https://github.com/swar/nba_api) — primary source of truth
- pybaseball GitHub (https://github.com/jldbc/pybaseball) — primary source of truth
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->
## Conventions

Conventions not yet established. Will populate as patterns emerge during development.
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->
## Architecture

Architecture not yet mapped. Follow existing patterns found in the codebase.
<!-- GSD:architecture-end -->

<!-- GSD:skills-start source:skills/ -->
## Project Skills

No project skills found. Add skills to any of: `.claude/skills/`, `.agents/skills/`, `.cursor/skills/`, `.github/skills/`, or `.codex/skills/` with a `SKILL.md` index file.
<!-- GSD:skills-end -->

<!-- GSD:workflow-start source:GSD defaults -->
## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:
- `/gsd-quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd-debug` for investigation and bug fixing
- `/gsd-execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->



<!-- GSD:profile-start -->
## Developer Profile

> Profile not yet configured. Run `/gsd-profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
