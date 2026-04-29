# Pitfalls Research

**Domain:** Sports ML research — NFL/NBA/MLB player performance prediction
**Researched:** 2026-04-29
**Confidence:** HIGH (pitfalls are well-established in sports analytics literature and empirically reproducible)

---

## Critical Pitfalls

### Pitfall 1: Selection Bias in NFL Combine Data

**What goes wrong:**
The combine dataset only contains players who were invited to the combine, which skews heavily toward drafted players — especially early-round picks. Models trained on this population do not generalize to the full distribution of NFL-caliber prospects, and the measurables-to-performance relationship is estimated on a highly filtered sample. Worse, players who attended but went undrafted are often dropped during a "merge with performance data" step, leaving only drafted players. The model then learns correlations that only hold within drafted players, not across the eligible prospect population.

**Why it happens:**
Researchers merge combine data with NFL career stats and drop NaN performance rows, inadvertently keeping only drafted players. The filtering looks like routine data cleaning rather than a modeling decision.

**How to avoid:**
Explicitly document the sample definition before any merge. Label three groups: (A) invited + drafted, (B) invited + undrafted, (C) not invited. Only discard group B/C if the research question explicitly concerns drafted players. If predicting "will this prospect succeed if drafted?", group B is signal-rich — undrafted players who had strong combines but no opportunity are exactly the false negatives the model must not treat as true negatives.

**Warning signs:**
- Post-merge row count drops more than 30% from raw combine rows
- All performance NaNs removed without an explicit comment explaining why
- Model evaluation shows suspiciously high R² (>0.5) on combine → career stats regression — likely a leaked or overfitted sample

**Phase to address:**
NFL foundation phase (first analysis). Data cleaning notebook must include a sample-definition cell that documents who is in and who is out before any model work.

---

### Pitfall 2: Survivorship Bias in Career Performance Targets

**What goes wrong:**
When the outcome variable is career or multi-season performance (e.g., career AV, career WAR, career PER), the dataset implicitly contains only players who survived long enough to accumulate meaningful stats. Players who washed out after one season have few rows of data and are often dropped or downweighted during aggregation. The model then predicts "what does a player who sticks around look like?" rather than "will this player stick around?"

**Why it happens:**
Researchers aggregate all available game-level data per player to get a single career row and drop players with insufficient seasons (e.g., < 2 seasons, < 100 games). This is numerically clean but methodologically flawed when the research question is about prospect evaluation.

**How to avoid:**
Define the target variable at a fixed horizon from draft year (e.g., performance in seasons 1–3 post-draft, regardless of whether the player is still active). Players who left the league in year 1 get a legitimate zero or low value, not a dropped row. For cross-sport work (NBA/MLB), the same principle applies — use a fixed window, not career aggregates.

**Warning signs:**
- Outcome variable is described as "career" anything (career touchdowns, career WAR, career PER)
- Sample size drops sharply after aggregation with no explanation
- Model performs much better on high-round picks than low-round picks (they survive longer, inflating their stats)

**Phase to address:**
NFL foundation phase, target variable definition step. Document the performance window explicitly in the notebook config cell.

---

### Pitfall 3: Data Leakage via Future Statistics

**What goes wrong:**
Features used in the model inadvertently contain information about the future. Common forms in sports ML: using career-aggregated stats as features (which include seasons after the predicted season), using cumulative statistics that roll forward into the prediction window, or training on a full-season stat to predict a mid-season outcome.

In combine-to-performance regression specifically, the leak is subtler: using "draft position" as a feature when predicting career success. Draft position encodes the collective wisdom of NFL scouts, which is itself a prediction of career success. The model learns to trust the draft, not the measurables.

**Why it happens:**
Draft position is readily available in the same dataset as combine data and seems like a legitimate contextual feature. Researchers include it without recognizing it is a proxy for the outcome variable.

**How to avoid:**
Audit every feature: "Was this value known on combine day, before draft day, or after career outcomes were realized?" Combine measurables (40-yard dash, vertical, weight) are known before the draft. Draft round, draft pick number, and team are known after combine but before career — include them only if the explicit goal is to explain draft outcomes, not career outcomes. Career stats, Pro Bowl selections, contract values are known after career — never features.

For time-series analyses (NBA game-by-game, MLB season-by-season): use strict temporal splits. Training data must be from seasons strictly earlier than the test period.

**Warning signs:**
- "draft_pick" or "draft_round" appears in the feature matrix for a career success model
- Cross-validation uses random splits rather than temporal splits on time-series data
- Model accuracy drops sharply when tested on a held-out recent season (future seasons the model never saw)

**Phase to address:**
NFL foundation phase feature engineering step. Every feature column should have a comment: `# known before draft` / `# known after draft` / `# post-career`.

---

### Pitfall 4: Small Sample Sizes Per Position Group

**What goes wrong:**
NFL combine data has roughly 300 players per draft class, but once split by position the samples are small: ~20–30 QBs, ~15–25 kickers/punters, ~30–40 OL per class. A regression fit on 5 combine classes of QB data is fitting a model to roughly 100–150 rows with 6–10 features. Position-specific models will overfit. Cross-position models will underfit or mask position-specific relationships (a fast 40 means different things for a CB vs. a TE).

**Why it happens:**
Researchers either (A) pool all positions and miss position-specific signal, or (B) split by position and overfit to tiny samples. Both paths produce unreliable estimates that look fine in-sample.

**How to avoid:**
Use hierarchical/mixed-effects models that pool information across positions while estimating position-specific slopes. If using plain OLS/sklearn, report confidence intervals or bootstrap standard errors — a coefficient with a 95% CI spanning zero is not a finding. Explicitly report N per position in every model summary. For positions with fewer than 50 historical examples in the training window, flag the model as exploratory only.

**Warning signs:**
- Model table shows results for "Kicker" with n=12 in the training set
- No standard errors or confidence intervals reported alongside coefficients
- R² reported for a position-specific model without noting sample size
- "All positions" model with a single intercept and no position dummy or interaction

**Phase to address:**
NFL foundation phase, model design. Config cell should include a minimum-N threshold: positions below threshold are excluded from modeling but included in a descriptive stats section.

---

### Pitfall 5: Mixing Per-Game and Per-Season Statistics Without Normalizing

**What goes wrong:**
When combining data across eras or players with different career lengths, raw counting stats (total touchdowns, total yards, total home runs) will always favor players with more games played. A receiver with 200 career games will have more receiving yards than a comparable receiver who played 100 games. Models trained on counting stats learn durability, not per-play quality.

Across eras, rule changes and pace inflation make raw stats non-comparable: NBA pace increased from ~88 possessions/game in 1999 to ~100+ in 2023, inflating all counting stats. MLB has had multiple designated hitter rule changes. NFL passing volume has increased structurally since the early 2000s.

**Why it happens:**
Public data APIs (nflverse, nba_api, pybaseball) return raw counting stats by default. Researchers use them directly without normalizing.

**How to avoid:**
Normalize by opportunity: yards per game, targets per game, rate stats (BA/OBP/SLG in MLB, TS% in NBA, QBR/DVOA in NFL). For cross-era comparisons, use era-adjusted stats (e.g., OPS+ in MLB, BPM in NBA) or include season and pace as covariates. Document the normalization in the config cell so it can be toggled.

**Warning signs:**
- Feature matrix contains "career_receiving_yards" without a corresponding games-played denominator
- NBA analysis spans pre-2015 and post-2018 without pace adjustment
- MLB pitcher analysis uses raw strikeout totals without adjusting for innings pitched

**Phase to address:**
NFL foundation phase feature engineering. NBA and MLB scaffold phases should note era-normalization as a required step before any modeling.

---

### Pitfall 6: Notebook Reproducibility Failures

**What goes wrong:**
Notebooks run correctly the first time but fail to reproduce six months later when a collaborator (or the original author) tries to re-run them. Common failure modes: cells run out of order and depend on hidden state, data is downloaded to a path that doesn't exist on another machine, library versions are unpinned and break on upgrade, random seeds are not set, and intermediate results are saved to disk mid-notebook and cells that use them assume they already exist.

**Why it happens:**
Notebooks encourage interactive exploration, which naturally produces out-of-order cell execution. Researchers don't notice because their kernel retains the state. The notebook "works" in every demo but cannot be run cold by anyone else.

**How to avoid:**
- Run notebooks top-to-bottom as a CI check before committing (`jupyter nbconvert --to notebook --execute`).
- Config cell at top: all paths, all seeds, all toggleable parameters. No hardcoded paths elsewhere.
- Pin dependencies in `requirements.txt` or `pyproject.toml` with exact versions for data-fetching libraries (nflverse wrappers, nba_api, pybaseball).
- Cache downloaded data to a `data/raw/` directory; the notebook checks if the file exists before fetching, so it can run offline.
- Set `random_state` on every sklearn model, train/test split, and bootstrap call.

**Warning signs:**
- `import` statements scattered across multiple cells (not all in cell 1)
- Hardcoded path like `/Users/mike/sports/data/combine.csv` anywhere in the notebook
- No `requirements.txt` or `pyproject.toml` in the repo
- A cell that reads a CSV produced by a different notebook without explanation
- Notebook has never been run from a fresh kernel (check: does it pass `--execute` from the command line?)

**Phase to address:**
Project scaffold phase (first). Establish the notebook conventions — config cell, data cache pattern, `--execute` test — before writing any analysis code. The CLAUDE.md notebook conventions already specify this pattern; enforce it from day one.

---

### Pitfall 7: API Rate Limits and Lack of Data Caching

**What goes wrong:**
Free sports data APIs (nba_api in particular) have aggressive rate limiting. A notebook that fetches player game logs for 500 players in a loop will hit rate limits, throw exceptions mid-execution, and leave the dataset in a partially-fetched state. Re-running fetches the same data again from scratch. Over a season of development, this wastes hours of fetch time and produces inconsistent cached datasets.

**Why it happens:**
Researchers write a `for player in players: fetch(player)` loop without a sleep, without checking if the file already exists, and without handling 429 errors.

**How to avoid:**
- Cache every API response to `data/raw/<source>/<resource_id>.json` or `.parquet` immediately after fetching.
- Before each fetch, check if the cached file exists; skip if it does.
- Add a `time.sleep(0.6)` between nba_api calls (the undocumented safe interval is roughly 1 request/second).
- Wrap fetch loops in try/except that logs failures to a separate `failed_ids.txt` so you can retry only failures.
- For pybaseball, use its built-in `cache=True` parameter where available.

**Warning signs:**
- API fetch loop has no `sleep` call
- `data/raw/` directory does not exist in the repo structure
- Notebook re-downloads all data every time it runs
- HTTPError or 429 exceptions visible in committed notebook output cells

**Phase to address:**
NFL foundation phase, data ingestion step. A `utils/fetch.py` module with caching and rate-limit handling should exist before any sport-specific notebooks are written.

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Use raw counting stats as features | No preprocessing required | Models measure durability, not quality; breaks cross-era comparisons | Never for modeling; fine for exploratory EDA |
| Omit undrafted players from combine dataset | Cleaner merge, no NaN targets | Selection bias baked in permanently; findings only valid for drafted players | Only if research question is explicitly about drafted players, documented explicitly |
| Random train/test split on time-series data | Balanced classes, simple code | Data leakage from future seasons inflates all metrics | Never for time-series; always use temporal split |
| Single global `.venv` for all three sports | Simpler setup | Dependency conflicts as NBA/MLB libraries accumulate; harder to isolate breakage | Acceptable at scaffold phase, should be revisited before NBA/MLB get real analyses |
| Unpinned dependencies | No maintenance burden | Breaks on library upgrades; notebook no longer reproducible | Never once analysis is committed for reference |
| Include draft position as a feature | Improves model fit immediately | Model learns to trust scouts, not measurables; defeats the research purpose | Only if explicitly studying "does draft position predict success beyond measurables?" |

---

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| nba_api | Calling endpoints in a tight loop, no sleep | `time.sleep(0.6)` between calls; cache responses to `data/raw/nba/` |
| nba_api | Using endpoint class names from old tutorials (they change across versions) | Pin nba_api version; check `nba_api.stats.endpoints` for current class list |
| pybaseball | Fetching Statcast data for full date ranges in one call | Use yearly chunks; Statcast returns large payloads and times out on multi-year calls |
| pybaseball | Ignoring the built-in `cache=True` / `verbose=False` parameters | Enable cache at notebook top: `pybaseball.cache.enable()` |
| nflverse (nflreadr Python wrapper) | Assuming data schema is stable across years | nflverse column names change between seasons; pin the data version or add schema validation |
| nflverse | Fetching combine data from a different source than play-by-play data, causing player ID mismatch | Use a single source for both combine and performance data, or resolve IDs explicitly via a crosswalk |

---

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Loading full Statcast pitch-by-pitch data into a pandas DataFrame | Notebook takes 10+ minutes to load; kernel OOM on < 16GB RAM | Load yearly chunks, filter to needed columns before concat | Any dataset > ~5M rows in-memory |
| Using sklearn GridSearchCV on a small sports dataset | CV runs fast but produces optimistically biased estimates | Use nested CV or at minimum a held-out test set never touched during tuning | Any time hyperparameters are tuned on the same split used for evaluation |
| Repeated full-dataset recomputes in notebook exploration | Iterating on model takes 5+ minutes per run | Checkpoint expensive computations (feature engineering) to parquet; reload if file exists | As soon as the dataset has > 50k rows or complex feature pipelines |
| Storing notebook outputs with large embedded DataFrames | Repo bloat; Git diffs unreadable | Clear output before committing (`jupyter nbconvert --ClearOutputPreprocessor.enabled=True`) | Immediately; even a single large Statcast notebook can add 50MB to a commit |

---

## Security Mistakes

This is a research project with no user-facing surface and no authentication. The only relevant security concern is credential handling.

| Mistake | Risk | Prevention |
|---------|------|------------|
| Committing API keys for paid data sources (if added later) | Key exposure in git history | Store in `~/.config/` (already established pattern in this environment); add `*.env` and `config.json` to `.gitignore` |
| Committing raw data files that contain PII or licensed data | License violation; repo takedown | `.gitignore` all `data/` directories; document that data must be fetched locally |

---

## UX Pitfalls

This is a research repo, not a user-facing product. "UX" here means researcher experience — the experience of opening a notebook cold and understanding what it does.

| Pitfall | Researcher Impact | Better Approach |
|---------|-------------------|-----------------|
| No config cell — parameters scattered through notebook | Re-running with different parameters requires hunting through 30 cells | Config cell at top: all paths, window sizes, position filters, seed |
| No markdown explanation of the research question before any code | Unclear what hypothesis is being tested; findings are uninterpretable without context | First cell is markdown: research question, data source, target variable definition |
| Model results printed inline without a summary table | Hard to compare across models or share findings | End-of-notebook summary cell that prints a clean DataFrame of all model metrics |
| No section headers in notebook | Can't navigate or skim; all cells look the same | Use `## Section Name` markdown cells as dividers: Data Loading, Feature Engineering, Modeling, Results |

---

## "Looks Done But Isn't" Checklist

- [ ] **Combine regression model:** Confirm undrafted players are handled explicitly (not silently dropped) — check row count before and after merge
- [ ] **Feature matrix:** Confirm no post-draft or post-career features are included — audit each column with a "when was this known?" annotation
- [ ] **Train/test split:** Confirm split is temporal (by draft class year), not random — verify test set contains only more recent draft classes
- [ ] **Position-specific results:** Confirm sample N is reported alongside every coefficient or metric — no results for positions with N < 30
- [ ] **Notebook reproducibility:** Confirm notebook runs clean top-to-bottom from a fresh kernel with no pre-existing cached state — run `jupyter nbconvert --to notebook --execute` on CI
- [ ] **Data caching:** Confirm `data/raw/` directory exists and all API fetches check for cached file before requesting
- [ ] **Stat normalization:** Confirm all features are rate/per-opportunity stats, not raw counting stats, or that counting stats are explicitly justified
- [ ] **Random seeds:** Confirm `random_state` is set on every split, model, and bootstrap call and is read from the config cell

---

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Selection bias discovered after model is complete | HIGH | Re-define sample, re-run all downstream steps; prior findings are likely invalid |
| Data leakage from draft position feature | MEDIUM | Drop the feature, retrain; if R² drops sharply, the prior model was learning scouts not measurables (document this as a finding) |
| Survivorship bias in target variable | HIGH | Redefine target to fixed-horizon window, re-fetch performance data, re-run models |
| Notebook not reproducible (hidden state) | MEDIUM | Restart kernel, run top-to-bottom, fix cells in order until clean; add `--execute` test |
| Missing data cache (API refetch required) | LOW | Add caching layer, re-fetch; annoying but recoverable |
| Unpinned dependencies broke on upgrade | MEDIUM | `pip freeze > requirements.txt` from known-good environment; pin and re-test |
| Raw counting stats used as features | LOW–MEDIUM | Add normalization step in feature engineering cell; refit models; compare results |

---

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Selection bias (combine dataset) | NFL foundation — data loading step | Row count audit cell shows combine vs. drafted counts; sample definition is documented |
| Survivorship bias (career target) | NFL foundation — target variable definition | Target column uses fixed horizon (e.g., `seasons_1_3_av`), not career aggregate |
| Data leakage (future features / draft position) | NFL foundation — feature engineering | Feature audit cell lists each column with "when known" annotation; draft position not in feature matrix |
| Small N per position | NFL foundation — modeling | Min-N filter in config cell; position sample sizes printed before model fit |
| Stat normalization | NFL foundation — feature engineering (also NBA/MLB scaffold) | All features are rate stats or have explicit normalization documented |
| Notebook reproducibility | Project scaffold (before any analysis) | `jupyter nbconvert --to notebook --execute` passes in CI or pre-commit check |
| API rate limits and caching | NFL foundation — data ingestion (also NBA/MLB scaffold) | `data/raw/` directory exists; fetch function checks cache before requesting |

---

## Sources

- Sports analytics community practice (established patterns in nflverse, pybaseball, nba_api ecosystems)
- NFL combine selection mechanism: combine invitations are issued by NFL teams; the population is pre-filtered before any data is collected
- Survivorship bias pattern: standard treatment in sports reference literature (e.g., Baseball Reference's use of fixed-window WAR for prospect evaluation vs. career WAR for Hall of Fame discussion)
- Data leakage via draft position: discussed in multiple sports analytics blog posts (The Athletic, Football Outsiders, Towards Data Science sports ML series)
- Notebook reproducibility: nbconvert `--execute` pattern is standard in reproducible research workflows
- nba_api rate limiting: documented in the nba_api GitHub issues; ~1 req/sec is the observed safe threshold
- pybaseball caching: documented in pybaseball README

---
*Pitfalls research for: Sports ML research — NFL/NBA/MLB player performance prediction*
*Researched: 2026-04-29*
