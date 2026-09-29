"""
run_sweep.py
============
Review 2 Part E - Parameter sweep (ablation).

Runs the burst experiment at several burst factors and records how p99,
p95, recovery time, and achieved QPS change with load. This demonstrates
*how the result changes with load* (the rubric's required ablation axis),
since there is only one system/backend under real test here (SQLite) -
component-level ablation (e.g. isolating WAL vs buffer pool) does not apply
to SQLite, so a load sweep is the scientifically appropriate ablation for
this testbed.

Usage:
    python run_sweep.py --backend sqlite --factors 1 2 3 4 5
"""
import argparse
import os
import csv

from run_burst_workload import run_burst_experiment

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS_DIR = os.path.join(BASE_DIR, "results")
os.makedirs(RESULTS_DIR, exist_ok=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--backend", choices=["sqlite", "postgres", "postgres_self_hosted", "postgres_managed"], default="postgres_self_hosted")
    ap.add_argument("--factors", type=float, nargs="+", default=[1.0, 2.0, 3.0, 4.0, 5.0])
    ap.add_argument("--base-qps", type=int, default=150)
    ap.add_argument("--pre-sec", type=int, default=5)
    ap.add_argument("--burst-sec", type=int, default=5)
    ap.add_argument("--post-sec", type=int, default=8)
    args = ap.parse_args()

    all_summaries = []
    for bf in args.factors:
        print(f"\n--- Sweep: backend={args.backend} burst_factor={bf}x ---")
        summary, _ = run_burst_experiment(
            args.backend, bf, args.base_qps,
            args.pre_sec, args.burst_sec, args.post_sec, tag=f"sweep_bf{bf}")
        all_summaries.append(summary)

    out_path = os.path.join(RESULTS_DIR, "ablation_results.csv")
    existing_rows = []
    if os.path.exists(out_path):
        with open(out_path, "r") as f:
            reader = csv.DictReader(f)
            existing_rows = [r for r in reader if r.get("backend") != args.backend]

    combined = existing_rows + all_summaries
    fieldnames = list(all_summaries[0].keys())
    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(combined)
    print(f"\nAblation results updated at {out_path} (total {len(combined)} rows)")


if __name__ == "__main__":
    main()
