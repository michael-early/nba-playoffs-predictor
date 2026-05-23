# MLB Research Stub

Placeholder for MLB analyses. v1 ships only a stub notebook + this README; the full Statcast clustering work is deferred to v2.

## Planned Analyses (v1 stub)

- **SCAF-02**: Stub notebook with a data-loading skeleton that runs top-to-bottom using `shared.cache.load_or_fetch` against `pybaseball`.

## Planned Analyses (v2, deferred)

- MLB Statcast clustering — batted-ball profile clustering on pybaseball data.

## Data Source

`pybaseball` — Statcast (Baseball Savant), FanGraphs, Baseball Reference. Caches locally by default; this project's `shared.cache` is the canonical cache.

## Conventions

- All data fetches go through `shared.cache.load_or_fetch`.
- Cache keys prefixed with `mlb_` (e.g., `"mlb_statcast_2023"`).
