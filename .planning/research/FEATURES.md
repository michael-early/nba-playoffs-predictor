# Feature Research

**Domain:** Multi-sport ML research repository (NFL/NBA/MLB player performance)
**Researched:** 2026-04-29
**Confidence:** MEDIUM — all tooling (WebSearch, WebFetch, Bash/Context7) denied in this session; findings drawn from training knowledge of the sports analytics ecosystem (cutoff Aug 2025). Flag for verification against nflverse docs, pybaseball docs, nba_api docs.

---

## Feature Landscape

### Table Stakes (Users Expect These)

Features any serious sports ML research repo includes. Absence signals the repo is a toy.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| EDA notebook per sport (distributions, missingness, correlations) | Standard starting point for any ML project; reviewers check this first | LOW | One notebook per sport folder; histograms, heatmaps, missing-value summaries |
| Data loading utilities (clean, typed, cached) | Raw data ingestion is boilerplate; repeating it in every notebook is noise | LOW | Shared `utils/` or per-sport `data.py`; cache to parquet |
| Positional segmentation for NFL | Combine metrics mean different things by position — treating all players together is a methodological error | LOW | Position groups: skill (WR/RB/TE), pass-rushers (DE/LB), OL, DB, QB |
| Target variable definition | "Career performance" must be operationalized — AV (Approximate Value), PFF grades, per-game stats | LOW-MEDIUM | Multiple targets are fine; document tradeoffs in notebook |
| Correlation analysis (Pearson + Spearman) | The most common first step; expected for combine → performance work | LOW | Include p-values and multiple-comparison correction (Bonferroni or BH) |
| Linear regression baseline | Establishes floor; every ML paper starts here | LOW | OLS via statsmodels; coefficient interpretation matters more than R² |
| Feature importance / coefficient plot | Makes findings legible to non-technical readers | LOW | Use matplotlib/seaborn; show confidence intervals |
| Train/test split with temporal awareness | Rookie year → career stats requires no data leakage (can't use 2024 outcomes to predict 2024 draft) | MEDIUM | Sort by draft year; use cohort-based splits, not random |
| Missingness analysis | Many combine drills are skipped (players opt out); ignoring this biases results | LOW | Flag opt-outs vs absent records; consider imputation vs exclusion |
| Notebook runs top-to-bottom with no side effects | Per PROJECT.md constraint; expected in research repos | LOW | Config cell first; `pip install -r requirements.txt` guard |

### Differentiators (Competitive Advantage)

Analyses that would distinguish this repo from "another combine stats notebook."

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Positional athleticism composite scores | Combine metrics are collinear; a PCA-derived athleticism index per position group is more interpretable and more predictive than raw drills | MEDIUM | PCA on standardized drill scores within position group; name the components (e.g., "explosion" vs "change-of-direction") |
| Drill opt-out analysis | Are combine opt-outs (top prospects skipping drills) biasing talent evaluation? Comparing career outcomes of opt-outs vs participants is novel and practically relevant | MEDIUM | Survival/selection analysis; inverse-probability weighting or propensity scoring to handle self-selection |
| Position-specific predictive feature profiles | Which drills predict success for each position group? (40-time matters for WR, irrelevant for OL) — published clearly per position | MEDIUM | Separate models per position; report which features are predictive/null per group |
| Career trajectory modeling (not just career totals) | Using season-by-season data to model peak year, longevity, and decline curves — more informative than aggregate AV | HIGH | Longitudinal panel model; mixed-effects or hierarchical Bayes |
| Draft round as confounder control | Better prospects go higher; not controlling for draft position confounds combine → performance regressions | MEDIUM | Include draft round/pick as covariate; or stratify analysis by round |
| NBA: role-based player clustering | Clustering NBA players by play-style (not just position) using box-score and play-by-play features; positions are poorly defined in modern NBA | MEDIUM | K-means or GMM on rate stats; name clusters from loadings |
| MLB: batted-ball profile clustering | Exit velocity, launch angle, pull/oppo% cluster into distinct batter archetypes; more predictive of future production than traditional stats | MEDIUM | Statcast-derived features via pybaseball; cluster then predict xwOBA |
| Cross-sport athleticism comparison | Shared physical measurables (vertical jump, 40-time equivalent) across sports; how do NFL combine scores relate to NBA pre-draft athleticism? | HIGH | Requires data normalization across measurement contexts; more of a research paper than a notebook |
| Reproducibility infrastructure | Pinned data snapshots + checksums so notebooks produce identical output 2 years later | LOW | `data/snapshots/` with hash file; date-stamped parquet |

### Anti-Features (Commonly Requested, Often Problematic)

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Single unified cross-sport model / framework | Seems elegant; reduces code duplication | NFL, NBA, MLB have fundamentally different data shapes, target variables, and research questions — forcing a common interface adds abstraction without insight | Keep sport folders independent per PROJECT.md; share only pure utilities (data loading helpers, plot styles) |
| Real-time / live data pipelines | Feels more "production-like" | This is a research repo; live pipelines add ops complexity (scheduling, failure handling, API rate limits) with no research value | Batch historical data only; document data vintage in notebook header |
| Prediction leaderboard / model deployment | Looks impressive | Scope creep; serving infrastructure is not research | Notebook outputs + saved model artifacts to disk; no serving layer |
| Betting-oriented framing | Combine research is adjacent to draft value / ADP | Explicitly out of scope per PROJECT.md; also muddies the research narrative | Frame all analyses as "what predicts career performance" not "who to draft-pick in fantasy" |
| Automated hyperparameter tuning (AutoML) | Reduces manual work | Obscures what the model learned; bad for interpretability-first research | Manual grid search or Optuna with documented search space; always inspect the winning config |
| Per-player prediction cards / dashboards | Shiny output to share | Notebook ≠ dashboard; building a UI is a different project | Export findings as CSV/LaTeX tables; a static PDF summary is fine |
| Cross-sport player comparison engine | Intuitively appealing ("Who is the NFL equivalent of LeBron?") | No defensible common measurement unit across sports; will produce misleading outputs | Document it as a long-run research question; don't build machinery for it yet |

---

## Feature Dependencies

```
[Positional segmentation]
    └──requires──> [Data loading utilities]
    └──required by──> [Position-specific predictive profiles]
    └──required by──> [Athleticism composite scores]

[Temporal train/test split]
    └──required by──> All predictive models
    └──requires──> [Data loading with draft year field]

[Correlation analysis]
    └──required by──> [Linear regression baseline]
    └──required by──> [Feature importance plots]

[Linear regression baseline]
    └──required by──> [Ensemble / nonlinear models] (if added later)
    └──enhances──> [Draft round as confounder control]

[Missingness analysis]
    └──required by──> [Opt-out bias analysis]
    └──informs──> [Imputation decisions in all models]

[Athleticism composite (PCA)]
    └──requires──> [Missingness handled / imputed]
    └──enhances──> [Position-specific predictive profiles]
```

### Dependency Notes

- **Positional segmentation requires data loading:** The position field must be clean and standardized (NFL position codes vary by source) before any position-grouped analysis.
- **Temporal split required by all models:** This must be established in shared utilities before any notebook builds a model; retrofitting it later causes silent data leakage.
- **Missingness analysis gates opt-out analysis:** Opt-out patterns are only interpretable once you can distinguish "player didn't test" (opt-out) from "drill not recorded" (data gap).
- **PCA composite requires imputed data:** PCA cannot handle NaN; imputation strategy must be decided and documented before running composites.

---

## NFL Combine: Metrics by Position Group

This section is specific to the first concrete analysis and informs which features to include per model.

### Metrics that matter per position

| Position Group | High-signal Drills | Low-signal / Often Skipped | Target Variables |
|---|---|---|---|
| WR / TE | 40-yard dash, vertical jump, 3-cone, short shuttle | Bench press (rarely tested / irrelevant) | Receiving yards/game, yards per route run, PFF receiving grade, career AV |
| RB | 40-yard dash, vertical, 3-cone, short shuttle | Bench press | Rushing yards/attempt, yards after contact, elusive rating, career AV |
| QB | 40-yard dash (minor), arm strength (not formally tested at combine) | Most drills | QB rating, EPA/play, career AV — note: combine is notoriously poor at predicting QB success |
| DE / Edge | 40-yard dash, vertical, 3-cone, broad jump, bench press | Short shuttle (less predictive) | Sacks/season, pressure rate, PFF pass-rush grade |
| DT | Bench press, 40-yard dash, broad jump | 3-cone (less relevant for interior) | Run-stop %, PFF run-defense grade |
| OL | Bench press (most meaningful single drill for OL), arm length, hand size | 40-yard dash | PFF pass-block grade, penalties |
| CB / S | 40-yard dash, vertical, 3-cone, short shuttle | Bench press | Passer rating allowed, PFF coverage grade |
| LB | 40-yard dash, vertical, 3-cone | Bench press | Tackles for loss, PFF coverage + run-stop grades |

**Research note (MEDIUM confidence):** The 3-cone and short shuttle are generally more predictive of coverage/change-of-direction ability than the 40, but the 40 gets outsized attention. Including both with PCA will surface this. Published work (Mulholland & Jensen 2014; Teramoto & Cross 2010) supports athleticism composites over individual drills — but verify citations before using.

---

## Standard NBA / MLB Metrics

### NBA — Standard Rate Stats (table stakes as features)

- **Offensive:** Points/36, AST%, USG%, TS%, 3PAr, FTr, ORB%
- **Defensive:** DRB%, STL%, BLK%, DBPM, Defensive Rating (team-adjusted)
- **Overall:** BPM, VORP, Win Shares/48, PER (note: PER is dated; VORP/BPM preferred)
- **Advanced:** On/off splits (+/-), lineup data, play-by-play-derived hustle stats (via nba_api)
- **Physical:** Height, wingspan, standing reach, weight, sprint/agility times (pre-draft combine)

### MLB — Standard Stats (table stakes as features)

- **Hitting (traditional):** BA, OBP, SLG, OPS, wRC+
- **Hitting (Statcast):** Exit velocity, launch angle, barrel %, xwOBA, xBA, sprint speed
- **Pitching (traditional):** ERA, FIP, xFIP, K%, BB%, K-BB%
- **Pitching (Statcast):** Spin rate, release extension, pitch movement profiles, stuff+
- **Fielding:** OAA (Outs Above Average), DRS, UZR (UZR increasingly questioned; OAA preferred)

---

## MVP Definition

### Launch With (v1) — NFL Combine Analysis

- [ ] Data loading for nflverse combine + career stats — the entire analysis depends on clean joined data
- [ ] Positional segmentation and missingness audit — without this, results are methodologically wrong
- [ ] EDA notebook: distributions, opt-out rates, position breakdowns
- [ ] Correlation analysis with multiple-comparison correction
- [ ] OLS regression (one per position group) with temporal train/test split
- [ ] Feature importance plots per position group
- [ ] NBA folder scaffold (README + empty notebook stub) — satisfies PROJECT.md requirement
- [ ] MLB folder scaffold (README + empty notebook stub) — satisfies PROJECT.md requirement

### Add After Validation (v1.x)

- [ ] PCA athleticism composites per position group — add once baseline correlations are established and you know which drills cluster
- [ ] Draft round as confounder — add when baseline model is done; easy covariate addition
- [ ] Opt-out bias analysis — add once missingness is well-understood

### Future Consideration (v2+)

- [ ] Career trajectory / panel models — requires multiple seasons of outcome data per player; significant data prep
- [ ] NBA role clustering — unblocked once NBA data loading is implemented
- [ ] MLB Statcast clustering — depends on pybaseball integration being validated

---

## Feature Prioritization Matrix

| Feature | Research Value | Implementation Cost | Priority |
|---------|---------------|---------------------|----------|
| Data loading + join (combine + career stats) | HIGH | MEDIUM | P1 |
| Positional segmentation | HIGH | LOW | P1 |
| Missingness / opt-out audit | HIGH | LOW | P1 |
| EDA notebook | HIGH | LOW | P1 |
| Correlation analysis | HIGH | LOW | P1 |
| OLS per position group | HIGH | LOW | P1 |
| Feature importance plots | MEDIUM | LOW | P1 |
| NBA scaffold | LOW | LOW | P1 (per PROJECT.md) |
| MLB scaffold | LOW | LOW | P1 (per PROJECT.md) |
| PCA athleticism composites | HIGH | MEDIUM | P2 |
| Draft round confounder | HIGH | LOW | P2 |
| Opt-out bias analysis | MEDIUM | MEDIUM | P2 |
| Career trajectory (panel) | HIGH | HIGH | P3 |
| NBA role clustering | HIGH | MEDIUM | P3 |
| MLB Statcast clustering | HIGH | MEDIUM | P3 |

**Priority key:**
- P1: Required for v1 NFL combine analysis + PROJECT.md requirements
- P2: Methodological improvements; add once baseline is working
- P3: Future sport-specific analyses

---

## Competitor Feature Analysis

The "competitors" here are reference sports analytics repos and notebooks.

| Feature | Typical GitHub Repo | Academic Papers | This Repo's Approach |
|---------|--------------------|-----------------|-----------------------|
| Combine → performance | Single-sport, no position segmentation, often uses career totals only | Segmented by position group; composite athleticism scores | Segmented + composites + temporal split (methodologically stronger) |
| Missing data handling | Drop rows with any NaN | Impute or flag separately | Distinguish opt-outs from gaps; document imputation choice explicitly |
| Target variable | Often AV (available, easy) | Mix of AV, PFF grades, per-game stats | Support multiple targets; document AV's known limitations |
| Reproducibility | Notebook with hardcoded paths | N/A | Config cells; cached parquet snapshots; pinned library versions |
| Scope | NFL only | Often NFL only | Multi-sport scaffold from day 1 |

---

## Sources

- nflverse documentation and nflreadr package README (not directly accessed this session — verify data field names before use)
- pybaseball README and Statcast documentation (not directly accessed — verify metric names)
- nba_api endpoint list (not directly accessed — verify endpoint availability)
- Mulholland, J. & Jensen, S.T. (2014). "Predicting the Draft and Career Success of Tight Ends in the National Football League." — MEDIUM confidence citation, verify existence
- Teramoto, M. & Cross, C.L. (2010). "Relative Importance of Performance Factors in Winning NFL Games." — MEDIUM confidence citation, verify existence
- Training knowledge of sports analytics community practices (Kaggle sports notebooks, The Athletic, FiveThirtyEight sports methodology writeups) — LOW confidence for specific details, MEDIUM for general patterns

---

*Feature research for: Sports ML Research Repository (NFL/NBA/MLB)*
*Researched: 2026-04-29*
*Confidence note: All external research tools blocked in this session. Findings based on training knowledge (cutoff Aug 2025). Verify nflverse data schema, pybaseball functions, and academic citations before building on them.*
