"""
run_iso_workload_benchmarks.py
================================
Novelty Research Framework: Iso-Workload Burst Geometry Benchmark
Course: Cloud Computing (CSE4001 / Sem 7) | P8: Managed vs Self-Hosted DBs Under Bursty Load

Mathematical Framework:
  We hold the total request energy constant across all burst shapes at exactly 3,600 excess queries:
      W_excess = integral[ t_start to t_end ] (lambda(t) - lambda_base) dt = 3,600 requests

Burst Shapes Evaluated:
  1. Sudden Step:      10 seconds at 360 QPS excess (10s * 360 QPS = 3,600 queries)
  2. Linear Ramp:      60 seconds acceleration / deceleration with integral = 3,600 queries
  3. Repeated Pulses:  3 pulses of 5s duration at 240 QPS excess (3 * 5s * 240 QPS = 3,600 queries)

Novelty Metrics:
  - BAF (Burst Amplification Factor):
        BAF = (burst_p99 - base_p99) / base_p99
  - AUC_H (Cumulative Tail Severity / Excess Latency Integral):
        excess_tail = np.maximum(0, p99_series - baseline_p99)
        AUC_H = np.trapz(excess_tail, time_series)
"""

import os
import sys
import time
import random
import argparse
import statistics
import csv
import numpy as np

# Robust trapezoidal numerical integration supporting both numpy 1.x and 2.x
trapz_integrate = getattr(np, 'trapezoid', getattr(np, 'trapz', None))

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(CURRENT_DIR)
SCRIPTS_DIR = os.path.join(PROJECT_DIR, 'scripts')
sys.path.insert(0, SCRIPTS_DIR)

from db_backend import Backend

RESULTS_DIR = os.path.join(CURRENT_DIR, 'results')
os.makedirs(RESULTS_DIR, exist_ok=True)

RECOVERY_HOLD_SEC = 3

# ============================================================================
# 1. THE 3 BURST SHAPE FUNCTIONS (Iso-Workload Request Energy: 3,600 Requests)
# ============================================================================

def sudden_step_burst(base_qps=150, burst_duration=10, burst_excess_qps=360):
    """
    Shape 1: Sudden Step Burst
    Duration: 10s at 360 QPS excess.
    Total Excess Energy: 10s * 360 QPS = 3,600 requests.
    """
    total_excess = burst_duration * burst_excess_qps  # Exactly 3,600
    schedule = [base_qps + burst_excess_qps] * burst_duration
    return schedule, total_excess


def linear_ramp_burst(base_qps=150, ramp_duration=60, total_excess=3600):
    """
    Shape 2: Linear Ramp Burst
    Duration: 60s continuous acceleration and gradual drain.
    Peak excess = 2 * total_excess / ramp_duration = 120 QPS.
    Total Excess Energy: Area under triangular ramp = 0.5 * 60 * 120 = 3,600 requests.
    """
    schedule = []
    half = ramp_duration // 2
    peak_excess = (2.0 * total_excess) / float(ramp_duration)
    for t in range(ramp_duration):
        if t < half:
            excess = peak_excess * (t + 1) / float(half)
        else:
            excess = peak_excess * (ramp_duration - t) / float(half)
        schedule.append(base_qps + int(round(excess)))
    return schedule, total_excess


def repeated_pulses_burst(base_qps=150, num_pulses=3, pulse_duration=5, pulse_excess_qps=240, pause_duration=5):
    """
    Shape 3: Repeated Pulses Burst
    Configuration: 3 distinct bursts of 5s duration at 240 QPS excess with 5s inter-pulse pauses.
    Total Pulse Duration: 3 * 5s = 15 seconds.
    Total Excess Energy: 15s * 240 QPS = 3,600 requests.
    """
    schedule = []
    for p in range(num_pulses):
        schedule.extend([base_qps + pulse_excess_qps] * pulse_duration)
        if p < num_pulses - 1:
            schedule.extend([base_qps] * pause_duration)
    total_excess = num_pulses * pulse_duration * pulse_excess_qps  # Exactly 3,600
    return schedule, total_excess


def get_burst_shape_schedule(shape_type, base_qps=150):
    if shape_type == 'sudden':
        return sudden_step_burst(base_qps=base_qps, burst_duration=10, burst_excess_qps=360)
    elif shape_type == 'ramp':
        return linear_ramp_burst(base_qps=base_qps, ramp_duration=60, total_excess=3600)
    elif shape_type == 'repeated':
        return repeated_pulses_burst(base_qps=base_qps, num_pulses=3, pulse_duration=5, pulse_excess_qps=240, pause_duration=5)
    else:
        raise ValueError(f"Unknown burst shape: {shape_type}")


# ============================================================================
# 2. WORKLOAD EXECUTION & TELEMETRY
# ============================================================================

def execute_db_query(backend, cur):
    acc_id = random.randint(1, 10000)
    cur.execute(backend.q("SELECT balance, customer_name FROM accounts WHERE id = ?"), (acc_id,))
    cur.fetchone()
    if random.random() < 0.25:
        amt = round(random.uniform(1.0, 20.0), 2)
        cur.execute(backend.q("UPDATE accounts SET balance = balance + ? WHERE id = ?"), (amt, acc_id))
        backend.commit()


def run_benchmark_second(backend, cur, target_qps):
    interval = 1.0 / max(target_qps, 1)
    window_end = time.time() + 1.0
    latencies = []
    while time.time() < window_end:
        t0 = time.perf_counter()
        execute_db_query(backend, cur)
        t1 = time.perf_counter()
        latencies.append((t1 - t0) * 1000.0)
        elapsed = t1 - t0
        if elapsed < interval:
            time.sleep(interval - elapsed)
    return latencies


# ============================================================================
# 3. RESEARCH NOVELTY MATH: BAF, AUC_H, & RECOVERY INTEGRALS
# ============================================================================

def compute_novelty_metrics(time_series, p99_series, baseline_p99, burst_p99, burst_end_time, post_burst_p99_series):
    """
    Computes BAF (Burst Amplification Factor) and AUC_H (Cumulative Tail Severity).
    """
    # 1. Burst Amplification Factor (BAF)
    # BAF: (burst_p99 - base_p99) / base_p99
    baf = (burst_p99 - baseline_p99) / max(baseline_p99, 0.001)

    # 2. AUC_H: Integral of max(0, p99(t) - p99_baseline) dt using numpy.trapz
    excess_tail = np.maximum(0, p99_series - baseline_p99)
    auc_h = float(trapz_integrate(excess_tail, time_series))

    # 3. Recovery Time Detection (1.5x baseline threshold for 3 consecutive seconds)
    recov_thresh = 1.5 * baseline_p99
    consecutive_ok = 0
    recovery_time_s = None
    
    for idx, (t, p99) in enumerate(zip(time_series, p99_series)):
        if t <= burst_end_time:
            continue
        if p99 <= recov_thresh:
            consecutive_ok += 1
            if consecutive_ok >= RECOVERY_HOLD_SEC:
                recovery_time_s = (t - RECOVERY_HOLD_SEC + 1) - burst_end_time
                break
        else:
            consecutive_ok = 0

    return {
        "BAF": round(float(baf), 4),
        "AUC_H": round(auc_h, 4),
        "recovery_time_s": recovery_time_s,
        "recovery_threshold_ms": round(recov_thresh, 3)
    }


# ============================================================================
# 4. EXPERIMENT HARNESS
# ============================================================================

def run_iso_workload_benchmark(backend_kind="postgres_managed", shape_type="sudden", base_qps=150, pre_sec=6, post_sec=15):
    print(f"\n{'='*75}")
    print(f"ISO-WORKLOAD BENCHMARK: Backend={backend_kind.upper()} | Shape={shape_type.upper()}")
    print(f"Holding Total Excess Energy Constant at W_excess = 3,600 Requests")
    print(f"{'='*75}")

    schedule, total_excess = get_burst_shape_schedule(shape_type, base_qps=base_qps)
    burst_duration = len(schedule)
    
    backend = Backend(backend_kind)
    cur = backend.cursor()
    backend.ensure_schema_and_seed(n_accounts=10000)

    time_records = []
    pre_p99s = []
    burst_end_step = pre_sec + burst_duration
    total_duration = pre_sec + burst_duration + post_sec

    for step in range(1, total_duration + 1):
        if step <= pre_sec:
            phase = "pre_burst"
            target_qps = base_qps
        elif step <= burst_end_step:
            phase = "burst"
            target_qps = schedule[step - pre_sec - 1]
        else:
            phase = "post_burst"
            target_qps = base_qps

        lats = run_benchmark_second(backend, cur, target_qps)
        lats.sort()
        p99 = float(np.percentile(lats, 99)) if lats else 0.0
        p50 = float(np.percentile(lats, 50)) if lats else 0.0

        if phase == "pre_burst":
            pre_p99s.append(p99)

        time_records.append({
            "second": step,
            "phase": phase,
            "shape": shape_type,
            "target_qps": target_qps,
            "actual_qps": len(lats),
            "p50_ms": round(p50, 3),
            "p99_ms": round(p99, 3)
        })
        print(f"[{step:02d}s | {phase:<10}] Shape={shape_type:<8} Target={target_qps:<4} Actual={len(lats):<4} p99={p99:6.2f}ms")

    backend.close()

    # Extract time series and latency arrays for numerical integration
    time_series = np.array([r["second"] for r in time_records], dtype=float)
    p99_series = np.array([r["p99_ms"] for r in time_records], dtype=float)

    baseline_p99 = statistics.mean(pre_p99s) if pre_p99s else 1.0
    burst_p99 = max(r["p99_ms"] for r in time_records if r["phase"] == "burst")
    post_burst_records = [r for r in time_records if r["phase"] == "post_burst"]

    # Calculate Novelty Mathematical Metrics (BAF, AUC_H)
    metrics = compute_novelty_metrics(
        time_series=time_series,
        p99_series=p99_series,
        baseline_p99=baseline_p99,
        burst_p99=burst_p99,
        burst_end_time=burst_end_step,
        post_burst_p99_series=post_burst_records
    )

    print(f"\n{'-'*75}")
    print(f"NOVELTY EMPIRICAL RESULTS ({shape_type.upper()}):")
    print(f"  • Baseline Steady p99:              {baseline_p99:.2f} ms")
    print(f"  • Peak Burst p99:                   {burst_p99:.2f} ms")
    print(f"  • Burst Amplification Factor (BAF): {metrics['BAF']}")
    print(f"  • Cumulative Tail Severity (AUC_H): {metrics['AUC_H']} ms*s")
    print(f"  • Recovery Time:                    {metrics['recovery_time_s']} s")
    print(f"  • Iso-Workload Energy:              {total_excess} requests")
    print(f"{'-'*75}\n")

    return metrics, time_records


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Iso-Workload Burst Geometry Research Benchmark")
    parser.add_argument("--backend", default="postgres_managed", choices=["postgres_managed", "sqlite", "postgres_docker"])
    parser.add_argument("--shape", default="all", choices=["sudden", "ramp", "repeated", "all"])
    parser.add_argument("--base-qps", type=int, default=150)
    args = parser.parse_args()

    shapes = ["sudden", "ramp", "repeated"] if args.shape == "all" else [args.shape]
    for s in shapes:
        run_iso_workload_benchmark(backend_kind=args.backend, shape_type=s, base_qps=args.base_qps)
