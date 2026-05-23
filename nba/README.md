# NBA Research Stub

Placeholder for NBA analyses. v1 ships only a stub notebook + this README; the full role-clustering / panel work is deferred to v2.

## Planned Analyses (v1 stub)

- **SCAF-01**: Stub notebook with a data-loading skeleton that runs top-to-bottom using `shared.cache.load_or_fetch` against `nba_api`.

## Planned Analyses (v2, deferred)

- NBA role clustering — k-means / GMM on box-score + play-by-play features.

## Data Source

`nba_api` — wraps stats.nba.com. Rate-limit aware: add `time.sleep` between calls.

## Conventions

- All data fetches go through `shared.cache.load_or_fetch`.
- Cache keys prefixed with `nba_` (e.g., `"nba_box_scores_2023_24"`).
