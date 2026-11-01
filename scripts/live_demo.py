"""
live_demo.py
============
Interactive, real-time Live Demonstration Script for Review 3 (21/10/26).
Fulfills Rubric Component 3:
"Live demonstration (2 marks): System runs during the review, not a recorded video."

Features:
- Live streaming ANSI terminal output with visual latency bar graph.
- Phase badges: [BASELINE], [4X SHOCK BURST], [POST-BURST RECOVERY].
- Real-time p99 calculation and automatic recovery time detection.
- Beautiful, professional final evaluation card with SLO compliance check.
- Runs in 20 seconds total.

Usage in Review:
    python scripts/live_demo.py
    python scripts/live_demo.py --backend sqlite
"""
import os
import sys
import time
import random
import statistics
import argparse

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, CURRENT_DIR)

from db_backend import Backend

# ANSI color codes for high-impact terminal presentation
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"

def render_ascii_bar(p99_val, max_scale=1500.0, bar_width=25):
    ratio = min(p99_val / max_scale, 1.0)
    filled = int(ratio * bar_width)
    empty = bar_width - filled
    if ratio > 0.7:
        color = RED
    elif ratio > 0.3:
        color = YELLOW
    else:
        color = GREEN
    return f"{color}{'■' * filled}{DIM}{'·' * empty}{RESET}"

def run_workload_sample(backend, cur, count=5):
    latencies = []
    for _ in range(count):
        acc_id = random.randint(1, 10000)
        t0 = time.perf_counter()
        if random.random() < 0.75:
            cur.execute(backend.q("SELECT balance, customer_name FROM accounts WHERE id = ?"), (acc_id,))
            cur.fetchone()
        else:
            amt = round(random.uniform(1.0, 20.0), 2)
            cur.execute(backend.q("UPDATE accounts SET balance = balance + ? WHERE id = ?"), (amt, acc_id))
            backend.commit()
        t1 = time.perf_counter()
        latencies.append((t1 - t0) * 1000.0)
    return latencies

def run_second_stream(backend, cur, target_qps):
    interval = 1.0 / max(target_qps, 1)
    window_end = time.time() + 1.0
    latencies = []
    while time.time() < window_end:
        t0 = time.perf_counter()
        acc_id = random.randint(1, 10000)
        if random.random() < 0.75:
            cur.execute(backend.q("SELECT balance, customer_name FROM accounts WHERE id = ?"), (acc_id,))
            cur.fetchone()
        else:
            amt = round(random.uniform(1.0, 20.0), 2)
            cur.execute(backend.q("UPDATE accounts SET balance = balance + ? WHERE id = ?"), (amt, acc_id))
            backend.commit()
        t1 = time.perf_counter()
        latencies.append((t1 - t0) * 1000.0)
        elapsed = t1 - t0
        if elapsed < interval:
            time.sleep(interval - elapsed)
    return latencies

def pct(sorted_vals, p):
    if not sorted_vals:
        return 0.0
    idx = min(int(len(sorted_vals) * p), len(sorted_vals) - 1)
    return sorted_vals[idx]

def run_live_demonstration(backend_kind="postgres_managed", base_qps=150, burst_multiplier=4.0, duration=20, slo_target=50.0):
    os.system("color" if os.name == "nt" else "")
    print(f"\n{BOLD}{CYAN}╔═════════════════════════════════════════════════════════════════════════════════╗{RESET}")
    print(f"{BOLD}{CYAN}║     PROJECT REVIEW 3: LIVE SYSTEM BENCHMARK DEMONSTRATION                       ║{RESET}")
    print(f"{BOLD}{CYAN}║     P8: Managed vs Self-Hosted Database Services Under Bursty Load              ║{RESET}")
    print(f"{BOLD}{CYAN}║     Students: Swayam Pani (23BCE1526) · Anamitra Shrivastava (23BCE5012)        ║{RESET}")
    print(f"{BOLD}{CYAN}╚═════════════════════════════════════════════════════════════════════════════════╝{RESET}\n")

    print(f"Connecting to database backend: {BOLD}{backend_kind}{RESET} ... ", end="", flush=True)
    try:
        backend = Backend(backend_kind)
        cur = backend.cursor()
        backend.ensure_schema_and_seed(n_accounts=10000)
        print(f"{GREEN}[ONLINE & SEEDED 10,000 ACCOUNTS]{RESET}\n")
    except Exception as e:
        print(f"{YELLOW}[FAILED TO CONNECT TO {backend_kind}: {e}]{RESET}")
        print(f"Falling back to local high-performance SQLite baseline engine...")
        backend_kind = "sqlite"
        backend = Backend("sqlite")
        cur = backend.cursor()
        backend.ensure_schema_and_seed(n_accounts=10000)

    # Compute timeline durations based on total duration
    baseline_sec = max(2, int(duration * 0.25))
    burst_sec = max(2, int(duration * 0.25))
    recovery_sec = max(3, duration - baseline_sec - burst_sec)

    print(f"Testbed Configuration:")
    print(f"  • Base Workload Arrival Rate:    {BOLD}{base_qps} QPS{RESET} (75% Read / 25% Write OLTP)")
    print(f"  • Transient Burst Shock:         {BOLD}{int(base_qps * burst_multiplier)} QPS ({burst_multiplier}x Multiplier){RESET}")
    print(f"  • Evaluation Timeline:           {baseline_sec}s Baseline ➔ {burst_sec}s Burst ➔ {recovery_sec}s Recovery ({duration}s Total)")
    print(f"  • Service Level Objective (SLO): p99 Tail Latency < {slo_target:.1f} ms\n")
    
    # -------------------------------------------------------------
    # ANSI Terminal ASCII Live-Graph Plotting Loop (Renders p99 bars)
    # -------------------------------------------------------------
    print(f"{BOLD}{'SEC':<4} | {'PHASE':<14} | {'TARGET':<10} | {'ACTUAL':<10} | {'p99 LATENCY':<12} | {'VISUAL TAIL SPREAD (p99)':<27} | {'STATUS'}{RESET}")
    print(f"{DIM}─" * 98 + f"{RESET}")

    timeline_records = []
    
    # Phase 1: Baseline Steady State
    for s in range(1, baseline_sec + 1):
        lats = run_second_stream(backend, cur, base_qps)
        lats.sort()
        p99 = pct(lats, 0.99)
        timeline_records.append({"sec": s, "phase": "BASELINE", "qps": base_qps, "actual": len(lats), "p99": p99})
        bar = render_ascii_bar(p99, max_scale=max(150.0, slo_target * 3))
        print(f"{s:02d}s  | {GREEN}BASELINE    {RESET} | {base_qps:<4} QPS   | {len(lats):<4} QPS   | {p99:7.2f} ms  | {bar} | {GREEN}STABLE{RESET}")

    base_p99_mean = statistics.mean([r["p99"] for r in timeline_records])
    recov_thresh = 1.5 * base_p99_mean
    burst_qps = int(base_qps * burst_multiplier)

    # Phase 2: Shock Burst Load
    for s in range(baseline_sec + 1, baseline_sec + burst_sec + 1):
        lats = run_second_stream(backend, cur, burst_qps)
        lats.sort()
        p99 = pct(lats, 0.99)
        timeline_records.append({"sec": s, "phase": "BURST", "qps": burst_qps, "actual": len(lats), "p99": p99})
        bar = render_ascii_bar(p99, max_scale=max(150.0, slo_target * 3))
        status = f"{RED}{BOLD}SHOCK BURST (+{int((burst_multiplier-1)*100)}%){RESET}" if s == baseline_sec + 1 else f"{RED}PEAK SATURATION{RESET}"
        print(f"{s:02d}s  | {RED}{BOLD}{int(burst_multiplier)}X BURST    {RESET} | {burst_qps:<4} QPS   | {len(lats):<4} QPS   | {p99:7.2f} ms  | {bar} | {status}")

    peak_p99 = max(r["p99"] for r in timeline_records if r["phase"] == "BURST")

    # Phase 3: Post-Burst Recovery Window
    recov_detected_at = None
    consec = 0
    burst_end_sec = baseline_sec + burst_sec
    for s in range(burst_end_sec + 1, burst_end_sec + recovery_sec + 1):
        lats = run_second_stream(backend, cur, base_qps)
        lats.sort()
        p99 = pct(lats, 0.99)
        timeline_records.append({"sec": s, "phase": "RECOVERY", "qps": base_qps, "actual": len(lats), "p99": p99})
        bar = render_ascii_bar(p99, max_scale=max(150.0, slo_target * 3))
        
        if p99 <= recov_thresh:
            consec += 1
            if consec >= 3 and recov_detected_at is None:
                recov_detected_at = (s - burst_end_sec) - 2 # 1st second it entered threshold
                status = f"{GREEN}{BOLD}RECOVERED ({recov_detected_at}s){RESET}"
            elif recov_detected_at is not None:
                status = f"{GREEN}STEADY STATE{RESET}"
            else:
                status = f"{YELLOW}STABILIZING ({consec}/3s){RESET}"
        else:
            consec = 0
            status = f"{YELLOW}DRAINING QUEUES{RESET}"
            
        print(f"{s:02d}s  | {YELLOW}RECOVERY    {RESET} | {base_qps:<4} QPS   | {len(lats):<4} QPS   | {p99:7.2f} ms  | {bar} | {status}")

    backend.close()

    if recov_detected_at is None:
        recov_detected_at = float(recovery_sec) # Upper bound

    baf = round(((peak_p99 - base_p99_mean) / base_p99_mean) / burst_multiplier, 3)
    
    # -------------------------------------------------------------
    # SLO Verification Check (SLO Target PASS/FAIL)
    # -------------------------------------------------------------
    slo_passed = peak_p99 <= slo_target

    print(f"\n{BOLD}{CYAN}╔═════════════════════════════════════════════════════════════════════════════════╗{RESET}")
    print(f"{BOLD}{CYAN}║                     LIVE BENCHMARK EMPIRICAL REPORT CARD                        ║{RESET}")
    print(f"{BOLD}{CYAN}╠═════════════════════════════════════════════════════════════════════════════════╣{RESET}")
    print(f"║  • Evaluated Architecture:           {BOLD}{backend_kind.upper():<43}{RESET}║")
    print(f"║  • Baseline Steady-State p99:        {BOLD}{base_p99_mean:7.2f} ms{RESET}{'':<36}║")
    print(f"║  • Peak Burst p99 Tail Latency:      {BOLD}{peak_p99:7.2f} ms{RESET}{'':<36}║")
    print(f"║  • Calculated Recovery Threshold:    {BOLD}{recov_thresh:7.2f} ms (1.5x Baseline){RESET}{'':<20}║")
    print(f"║  • Empirical Recovery Time:          {BOLD}{recov_detected_at} seconds{RESET}{'':<39}║")
    print(f"║  • Burst Amplification Factor (BAF): {BOLD}{baf:<43}{RESET}║")
    slo_badge = f"{GREEN}{BOLD}PASS (Peak p99 {peak_p99:.1f}ms <= {slo_target:.1f}ms SLO){RESET}" if slo_passed else f"{RED}{BOLD}FAIL (Peak p99 {peak_p99:.1f}ms > {slo_target:.1f}ms SLO){RESET}"
    print(f"║  • Latency SLO Verification:         {slo_badge:<52}║")
    print(f"{BOLD}{CYAN}╚═════════════════════════════════════════════════════════════════════════════════╝{RESET}\n")

# -----------------------------------------------------------------
# CLI Argument Parser (--backend, --duration, --burst-multiplier)
# -----------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Live Review 3 Interactive Benchmark Demonstration")
    parser.add_argument("--backend", default="postgres_managed", choices=["postgres_managed", "sqlite", "postgres_self_hosted", "postgres_docker"],
                        help="Target DB: postgres_managed (Neon AWS Ohio), sqlite, or postgres_docker")
    parser.add_argument("--duration", type=int, default=20,
                        help="Total experiment duration in seconds (default: 20)")
    parser.add_argument("--burst-multiplier", "--burst-factor", dest="burst_multiplier", type=float, default=4.0,
                        help="Load multiplier during burst phase (default: 4.0x)")
    parser.add_argument("--base-qps", type=int, default=150,
                        help="Baseline query rate in QPS (default: 150)")
    parser.add_argument("--slo-target", "--slo", dest="slo_target", type=float, default=50.0,
                        help="SLO latency target threshold in ms (default: 50.0ms PASS/FAIL check)")
    args = parser.parse_args()
    
    run_live_demonstration(
        backend_kind=args.backend,
        base_qps=args.base_qps,
        burst_multiplier=args.burst_multiplier,
        duration=args.duration,
        slo_target=args.slo_target
    )
