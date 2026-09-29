# P8 — Managed vs Self-Hosted Database Services Under Bursty Load
### Review 2: Implementation and Preliminary Results

Authors: Swayam Pani (23BCE1526), Anamitra Shrivastava (23BCE5012)
Faculty: Dr Indra Priyadarshini S

---

## 1. Project description

This project compares a managed cloud database service against a self-hosted
containerized PostgreSQL deployment under **bursty** load, measuring p99 tail
latency, post-burst recovery time, administrative labor, and 3-year total
cost of ownership (TCO). Review 1 defined the objectives (O1–O4) and
hypothesis; Review 2 implements the bursty-workload experiment, a burst-factor
ablation sweep, and the TCO model, and reports what could and could not be
measured in the current environment.

## 2. Important correction from Review 1

Review 1's slides described the self-hosted engine as "PostgreSQL 15-alpine
in Docker." **The benchmark code that actually produced Review 1's numbers
(`run_baseline.py`) connects to a local SQLite file (`testbed_db.sqlite`),
not to Postgres or Docker.** The `docker/` folder (compose file + schema)
was written but never wired into the benchmark scripts.

Review 2 fixes this by:
- Relabeling every already-existing measured result as **self-hosted
  SQLite**, not Postgres.
- Adding a `--backend {sqlite,postgres}` flag (`scripts/db_backend.py`) so
  the same benchmark code can run against the Dockerized Postgres container
  once it's actually started.
- Marking every Postgres-backend and every "managed cloud DB" result as
  **PENDING** — not fabricated — until someone with Docker/cloud access runs
  it.

## 3. Architecture

```
docker/                  Docker Compose + config for Postgres 15-alpine (not yet exercised)
  docker-compose.yml
  postgres.conf
scripts/
  init_schema.sql        Postgres schema (accounts, transactions, audit_logs)
  db_backend.py           Backend abstraction: sqlite (measured) / postgres (pending)
  run_baseline.py         Steady-state QPS scenarios (O-baseline, reproduces Review 1)
  run_burst_workload.py   Pre-burst / burst / post-burst experiment, p95/p99, recovery time (O1, O2)
  run_sweep.py             Burst-factor ablation sweep (Part E)
  build_results_summary.py Consolidates logs -> results/results_summary.csv
  tco_model.py             3-year TCO sensitivity sweep + chart (O4)
  generate_plots.py        All figures in results/figures/
results/
  results_summary.csv
  ablation_results.csv
  tco_results.csv
  admin_effort.csv         Template - see Part F below, mostly PENDING
  burst_timeseries_*.csv   Raw per-second time series for every burst run
  figures/                 PNG charts
logs/                      Timestamped run logs (append-only)
```

## 4. Prerequisites

- Python 3.10+
- `pip install -r requirements.txt`
- Docker + Docker Compose, **only** if you want to exercise the Postgres
  backend (`docker compose -f docker/docker-compose.yml up -d`)

## 5. How to run everything

```bash
# Steady-state baseline (reproduces Review 1's 3 scenarios)
python scripts/run_baseline.py

# Single bursty-workload experiment (O1 + O2)
python scripts/run_burst_workload.py --backend sqlite --burst-factor 4.0

# Burst-factor ablation sweep (Part E)
python scripts/run_sweep.py --backend sqlite --factors 1 2 3 4 5

# Consolidate logs into results/results_summary.csv
python scripts/build_results_summary.py

# 3-year TCO sensitivity model + chart (O4)
python scripts/tco_model.py

# All figures
python scripts/generate_plots.py
```

### Running the Postgres backend (not yet done — instructions for whoever has Docker access)

```bash
docker compose -f docker/docker-compose.yml up -d
pip install psycopg2-binary
python scripts/run_burst_workload.py --backend postgres --burst-factor 4.0
```

## 6. Where results are stored

- `results/results_summary.csv` — one row per steady-state scenario and per
  ablation point, in the schema the Review 2 rubric asks for.
- `results/ablation_results.csv` — burst-factor sweep (1x–5x).
- `results/tco_results.csv` — TCO sensitivity sweep.
- `results/admin_effort.csv` — **mostly PENDING**; see Part F below.
- `results/figures/*.png` — every chart referenced in this README and the
  Review 2 slides.

## 7. Measured vs assumed vs pending

| Item | Status |
|---|---|
| Steady-state QPS/latency, self-hosted SQLite | **Measured** (this run, this container) |
| Bursty workload p95/p99 time series, self-hosted SQLite | **Measured** (this run, this container) |
| Recovery time, self-hosted SQLite | **Measured**, using an explicit, pre-declared threshold (1.5× pre-burst mean p99, held for 3 consecutive seconds) |
| Burst-factor ablation (1x–5x), self-hosted SQLite | **Measured** |
| Self-hosted Postgres (Docker) results | **PENDING** — code is ready (`--backend postgres`), not yet executed; no Docker/network access in the environment that produced this Review |
| Managed cloud DB (RDS / Cloud SQL) results | **PENDING** — no managed account was provisioned; no results of any kind exist for this arm |
| Administrative effort (`admin_effort.csv`) | **PENDING** — see Part F; no wall-clock timings have been logged yet, so the file is a template with no invented numbers |
| TCO infrastructure costs ($150/mo managed, $45/mo self-hosted) | **Assumption**, not a vendor invoice or listed price — placeholder figures carried over from the Review-1-era `tco_model.py`. Must be replaced with actual RDS/Cloud SQL list pricing and actual VM/hosting cost before the TCO numbers can be presented as more than illustrative. |
| DBA hours/month (3 managed / 25 self-hosted) | **Assumption**, not measured — same caveat |

## 8. Threats to validity

**What this experiment CAN demonstrate:**
- The shape of p95/p99 latency before, during, and after a load burst on a
  single-writer SQLite-backed OLTP-like workload.
- How peak p99 and recovery time change as burst intensity increases
  (1x–5x), on one machine.
- A transparent, auditable recovery-time definition and threshold.

**What this experiment CANNOT demonstrate (yet):**
- Any claim about Postgres or a managed cloud database's actual latency or
  recovery behavior — no such data has been collected.
- The original hypothesis (managed reduces p99 by ≥45%, recovery by ≥60%)
  is **untested**, because the managed arm has never been run.
- The TCO crossover point is **illustrative only** — it is a function of the
  assumed cost inputs above, not observed billing or measured admin hours.
- Results come from a single container/VM run once per configuration, not
  averaged over repeated trials, and from a cloud sandbox whose I/O and CPU
  headroom likely differ substantially from the original Windows machine
  used for Review 1 (steady-state numbers here are faster and less variable
  than Review 1's) and from any production environment.
- SQLite is a single-process, single-writer embedded database. It does not
  have the client/server connection pooling, network round-trip, or
  multi-backend lock contention that a real Postgres/managed deployment
  has — several burst runs here showed **no significant p99 spike during the
  burst window itself** (see `results/figures/burst_p99_timeseries.png`),
  which is plausibly a property of SQLite's architecture and this
  environment's I/O headroom, not evidence that bursts are harmless in
  general. This is the central open question Postgres/managed testing would
  resolve.
- No query errors, timeouts, or connection-pool exhaustion are modeled;
  `error_rate` is recorded as `0.0` throughout because the harness does not
  yet inject or detect failures.

## 9. Reproducibility

Every number in `results/*.csv` is traceable to:
1. The script that produced it (see table above / section 5),
2. The log file in `logs/` with a timestamp,
3. This README's "Measured vs assumed vs pending" table for what kind of
   number it is.

No number in this repository was hand-typed or invented.

## 10. Version control

See "Git commands" in the final chat response for the exact commands to
initialize and commit this repository.
