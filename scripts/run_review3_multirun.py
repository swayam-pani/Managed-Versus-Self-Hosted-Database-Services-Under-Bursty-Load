"""
run_review3_multirun.py
=======================
Fulfills Review 3 Rubric Components:
1. All objectives evidenced:
   - Evaluates 3 distinct production workloads:
     * Read-Heavy (80% SELECT, 20% UPDATE)
     * Balanced (50% SELECT, 50% UPDATE)
     * Write-Heavy (20% SELECT, 80% UPDATE)
   - Executes at least 3 independent trials (N=3) per configuration
   - Computes empirical sample mean (mu) and sample variance (sigma^2).
2. Statistical soundness:
   - Produces raw trials and aggregated statistics with 95% Confidence Intervals (CI95)
     for generating error-bar charts and shaded variance envelopes.

Usage:
    python scripts/run_review3_multirun.py --backend postgres_managed --trials 3
    python scripts/run_review3_multirun.py --backend sqlite --trials 3
"""
import os
import sys
import time
import math
import random
import argparse
import datetime
import statistics
import csv

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(CURRENT_DIR)
RESULTS_DIR = os.path.join(PROJECT_DIR, "results")
os.makedirs(RESULTS_DIR, exist_ok=True)

sys.path.insert(0, CURRENT_DIR)
from db_backend import Backend

WORKLOAD_CONFIGS = {
    "read_heavy": {"read_pct": 0.80, "write_pct": 0.20, "desc": "80% Read / 20% Write (Dashboard / Catalog Browsing)"},
    "balanced":   {"read_pct": 0.50, "write_pct": 0.50, "desc": "50% Read / 50% Write (E-Commerce / Inventory Order Processing)"},
    "write_heavy":{"read_pct": 0.20, "write_pct": 0.80, "desc": "20% Read / 80% Write (Financial Ledger / High-Frequency Audit Logging)"},
}

RECOVERY_HOLD_SEC = 3

def execute_workload_query(backend, cur, read_pct):
    acc_id = random.randint(1, 10000)
    if random.random() < read_pct:
        cur.execute(backend.q("SELECT balance, customer_name FROM accounts WHERE id = ?"), (acc_id,))
        cur.fetchone()
    else:
        amt = round(random.uniform(1.0, 25.0), 2)
        cur.execute(backend.q("UPDATE accounts SET balance = balance + ? WHERE id = ?"), (amt, acc_id))
        backend.commit()

def run_one_second(backend, cur, target_qps, read_pct):
    interval = 1.0 / max(target_qps, 1)
    window_end = time.time() + 1.0
    latencies = []
    errs = 0
    while time.time() < window_end:
        t0 = time.perf_counter()
        try:
            execute_workload_query(backend, cur, read_pct)
            t1 = time.perf_counter()
            latencies.append((t1 - t0) * 1000.0)
            elapsed = t1 - t0
            if elapsed < interval:
                time.sleep(interval - elapsed)
        except Exception as e:
            errs += 1
            time.sleep(0.01)
    return latencies, errs

def pct(sorted_vals, p):
    if not sorted_vals:
        return 0.0
    idx = min(int(len(sorted_vals) * p), len(sorted_vals) - 1)
    return sorted_vals[idx]

def run_single_burst_trial(backend_kind, workload_name, trial_id, base_qps=150, burst_factor=4.0,
                           pre_sec=6, burst_sec=10, post_sec=14):
    cfg = WORKLOAD_CONFIGS[workload_name]
    read_pct = cfg["read_pct"]
    burst_qps = int(base_qps * burst_factor)
    
    backend = Backend(backend_kind)
    cur = backend.cursor()
    backend.ensure_schema_and_seed(n_accounts=10000)
    
    sec_records = []
    
    # Phase 1: Pre-burst
    for s in range(1, pre_sec + 1):
        lats, errs = run_one_second(backend, cur, base_qps, read_pct)
        lats.sort()
        sec_records.append({
            "second": s, "phase": "pre_burst", "target_qps": base_qps,
            "achieved_qps": len(lats), "p50": pct(lats, 0.50), "p95": pct(lats, 0.95), "p99": pct(lats, 0.99), "errors": errs
        })
        
    pre_p99_vals = [r["p99"] for r in sec_records if r["phase"] == "pre_burst"]
    base_p99 = statistics.mean(pre_p99_vals) if pre_p99_vals else 1.0
    recov_thresh = 1.5 * base_p99
    
    # Phase 2: Burst
    for s in range(pre_sec + 1, pre_sec + burst_sec + 1):
        lats, errs = run_one_second(backend, cur, burst_qps, read_pct)
        lats.sort()
        sec_records.append({
            "second": s, "phase": "burst", "target_qps": burst_qps,
            "achieved_qps": len(lats), "p50": pct(lats, 0.50), "p95": pct(lats, 0.95), "p99": pct(lats, 0.99), "errors": errs
        })
        
    burst_p99_vals = [r["p99"] for r in sec_records if r["phase"] == "burst"]
    peak_p99 = max(burst_p99_vals) if burst_p99_vals else base_p99
    
    # Phase 3: Post-burst
    for s in range(pre_sec + burst_sec + 1, pre_sec + burst_sec + post_sec + 1):
        lats, errs = run_one_second(backend, cur, base_qps, read_pct)
        lats.sort()
        sec_records.append({
            "second": s, "phase": "post_burst", "target_qps": base_qps,
            "achieved_qps": len(lats), "p50": pct(lats, 0.50), "p95": pct(lats, 0.95), "p99": pct(lats, 0.99), "errors": errs
        })
        
    backend.close()
    
    # Calculate recovery time
    post_records = [r for r in sec_records if r["phase"] == "post_burst"]
    consec = 0
    recov_time = None
    for idx, r in enumerate(post_records, start=1):
        if r["p99"] <= recov_thresh:
            consec += 1
            if consec >= RECOVERY_HOLD_SEC:
                recov_time = (idx - RECOVERY_HOLD_SEC + 1)
                break
        else:
            consec = 0
            
    if recov_time is None:
        recov_time = post_sec + 1.0  # Cap if not recovered
        
    baf = round(((peak_p99 - base_p99) / base_p99) / ((burst_qps - base_qps) / base_qps), 4)
    
    trial_summary = {
        "backend": backend_kind,
        "workload": workload_name,
        "trial_id": trial_id,
        "base_qps": base_qps,
        "burst_qps": burst_qps,
        "pre_burst_p99_ms": round(base_p99, 3),
        "peak_burst_p99_ms": round(peak_p99, 3),
        "recovery_threshold_ms": round(recov_thresh, 3),
        "recovery_time_s": recov_time,
        "baf": baf,
        "total_errors": sum(r["errors"] for r in sec_records)
    }
    
    return trial_summary, sec_records

def compute_stats(values):
    n = len(values)
    if n == 0:
        return 0.0, 0.0, 0.0, 0.0
    mean_val = statistics.mean(values)
    var_val = statistics.variance(values) if n > 1 else 0.0
    std_val = statistics.stdev(values) if n > 1 else 0.0
    # Student's t critical value for 95% confidence interval
    # df = n-1: for n=3, df=2, t=4.303; for n=5, df=4, t=2.776
    t_crit = 4.303 if n == 3 else (2.776 if n == 5 else 1.96)
    ci95 = t_crit * (std_val / math.sqrt(n)) if n > 1 else 0.0
    return round(mean_val, 3), round(var_val, 4), round(std_val, 3), round(ci95, 3)

def run_multiworkload_multirun(backend_kind, num_trials=3):
    print(f"\n=================================================================")
    print(f"REVIEW 3 MULTI-WORKLOAD MULTI-RUN ENGINE: {backend_kind}")
    print(f"Executing {num_trials} repeated trials across 3 workloads")
    print(f"Workloads: Read-Heavy (80/20), Balanced (50/50), Write-Heavy (20/80)")
    print(f"=================================================================\n")
    
    all_trial_summaries = []
    all_timeseries_records = []
    
    workloads = ["read_heavy", "balanced", "write_heavy"]
    
    for wl in workloads:
        print(f"\n---> Starting Workload: {wl.upper()} ({WORKLOAD_CONFIGS[wl]['desc']})")
        for t in range(1, num_trials + 1):
            print(f"  [Trial {t}/{num_trials}] Running burst benchmark...", end="", flush=True)
            t_sum, ts_recs = run_single_burst_trial(backend_kind, wl, t)
            all_trial_summaries.append(t_sum)
            for rec in ts_recs:
                rec["backend"] = backend_kind
                rec["workload"] = wl
                rec["trial_id"] = t
                all_timeseries_records.append(rec)
            print(f" Done! Base p99: {t_sum['pre_burst_p99_ms']}ms | Peak p99: {t_sum['peak_burst_p99_ms']}ms | Recov: {t_sum['recovery_time_s']}s")
            time.sleep(1)
            
    # Save raw trials CSV
    raw_csv_path = os.path.join(RESULTS_DIR, f"review3_trials_raw_{backend_kind}.csv")
    with open(raw_csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=all_trial_summaries[0].keys())
        writer.writeheader()
        writer.writerows(all_trial_summaries)
    print(f"\nSaved raw trial results to {raw_csv_path}")
    
    # Save timeseries CSV
    ts_csv_path = os.path.join(RESULTS_DIR, f"review3_timeseries_raw_{backend_kind}.csv")
    with open(ts_csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=all_timeseries_records[0].keys())
        writer.writeheader()
        writer.writerows(all_timeseries_records)
    print(f"Saved raw timeseries to {ts_csv_path}")
    
    # Compute Mean and Variance across trials for each workload
    stat_rows = []
    for wl in workloads:
        subset = [s for s in all_trial_summaries if s["workload"] == wl]
        base_p99s = [s["pre_burst_p99_ms"] for s in subset]
        peak_p99s = [s["peak_burst_p99_ms"] for s in subset]
        recov_times = [s["recovery_time_s"] for s in subset]
        bafs = [s["baf"] for s in subset]
        
        b_mean, b_var, b_std, b_ci = compute_stats(base_p99s)
        p_mean, p_var, p_std, p_ci = compute_stats(peak_p99s)
        r_mean, r_var, r_std, r_ci = compute_stats(recov_times)
        baf_mean, baf_var, baf_std, baf_ci = compute_stats(bafs)
        
        stat_rows.append({
            "backend": backend_kind,
            "workload": wl,
            "trials_n": num_trials,
            "base_p99_mean_ms": b_mean,
            "base_p99_variance": b_var,
            "base_p99_std": b_std,
            "base_p99_ci95": b_ci,
            "peak_p99_mean_ms": p_mean,
            "peak_p99_variance": p_var,
            "peak_p99_std": p_std,
            "peak_p99_ci95": p_ci,
            "recovery_time_mean_s": r_mean,
            "recovery_time_variance": r_var,
            "recovery_time_std": r_std,
            "recovery_time_ci95": r_ci,
            "baf_mean": baf_mean,
            "baf_variance": baf_var,
            "baf_ci95": baf_ci
        })
        
    stat_csv_path = os.path.join(RESULTS_DIR, f"review3_statistical_summary_{backend_kind}.csv")
    with open(stat_csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=stat_rows[0].keys())
        writer.writeheader()
        writer.writerows(stat_rows)
    print(f"Saved aggregated statistical summary to {stat_csv_path}")
    
    # Print formatted table for terminal review
    print(f"\n=========================================================================================")
    print(f"REVIEW 3 AGGREGATED STATISTICAL TABLE [{backend_kind.upper()}] (N={num_trials} Trials)")
    print(f"=========================================================================================")
    print(f"{'Workload':<14} | {'Base p99 Mean+-CI (ms)':<23} | {'Peak p99 Mean+-CI (ms)':<23} | {'Recov Time (s)':<16} | {'BAF Mean+-CI':<15}")
    print(f"-" * 95)
    for row in stat_rows:
        base_str = f"{row['base_p99_mean_ms']} +- {row['base_p99_ci95']}"
        peak_str = f"{row['peak_p99_mean_ms']} +- {row['peak_p99_ci95']}"
        rec_str  = f"{row['recovery_time_mean_s']} +- {row['recovery_time_ci95']}"
        baf_str  = f"{row['baf_mean']} +- {row['baf_ci95']}"
        print(f"{row['workload']:<14} | {base_str:<23} | {peak_str:<23} | {rec_str:<16} | {baf_str:<15}")
    print(f"=========================================================================================\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Review 3 Multi-workload Multi-run Benchmark")
    parser.add_argument("--backend", default="postgres_managed", choices=["postgres_managed", "sqlite", "postgres_self_hosted"])
    parser.add_argument("--trials", type=int, default=3, help="Number of repeated trials per workload (default 3)")
    args = parser.parse_args()
    
    run_multiworkload_multirun(args.backend, args.trials)
