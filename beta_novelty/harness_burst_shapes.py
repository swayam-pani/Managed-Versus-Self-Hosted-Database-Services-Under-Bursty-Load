import os, sys, time, random, statistics, csv

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(CURRENT_DIR)
SCRIPTS_DIR = os.path.join(PROJECT_DIR, 'scripts')
sys.path.insert(0, SCRIPTS_DIR)

from db_backend import Backend

RESULTS_DIR = os.path.join(CURRENT_DIR, 'results')
FIG_DIR = os.path.join(RESULTS_DIR, 'figures')
os.makedirs(RESULTS_DIR, exist_ok=True)
os.makedirs(FIG_DIR, exist_ok=True)

RECOVERY_HOLD_SEC = 3

def run_one_query(backend, cur):
    acc_id = random.randint(1, 10000)
    cur.execute(backend.q("SELECT balance, customer_name FROM accounts WHERE id = ?"), (acc_id,))
    cur.fetchone()
    if random.random() < 0.25:
        amt = round(random.uniform(1.0, 20.0), 2)
        cur.execute(backend.q("UPDATE accounts SET balance = balance + ? WHERE id = ?"), (amt, acc_id))
        backend.commit()

def run_second(backend, cur, target_qps):
    interval = 1.0 / max(target_qps, 1)
    window_end = time.time() + 1.0
    latencies = []
    while time.time() < window_end:
        q0 = time.perf_counter()
        run_one_query(backend, cur)
        q1 = time.perf_counter()
        latencies.append((q1 - q0) * 1000.0)
        elapsed = q1 - q0
        if elapsed < interval:
            time.sleep(interval - elapsed)
    return latencies

def pct(sorted_vals, p):
    if not sorted_vals:
        return 0.0
    idx = min(int(len(sorted_vals) * p), len(sorted_vals) - 1)
    return sorted_vals[idx]

def get_burst_schedule(shape_type, base_qps=150, burst_window_sec=12):
    if shape_type == 'sudden':
        return [base_qps + 300] * burst_window_sec
    elif shape_type == 'ramp':
        extra = [50, 100, 200, 350, 500, 550, 550, 500, 350, 200, 100, 50]
        return [base_qps + e for e in extra]
    elif shape_type == 'repeated':
        extra = [450, 450, 450, 450, 0, 0, 0, 0, 450, 450, 450, 450]
        return [base_qps + e for e in extra]
    else:
        raise ValueError(f'Unknown burst shape: {shape_type}')

def run_shape_experiment(backend_kind, shape_type, base_qps=150, pre_sec=6, burst_sec=12, post_sec=12):
    print(f"\n[START] Shape Experiment: backend={backend_kind} | shape={shape_type.upper()} | Iso-Extra=3600 reqs")
    backend = Backend(backend_kind)
    backend.ensure_schema_and_seed()
    cur = backend.cursor()
    
    burst_targets = get_burst_schedule(shape_type, base_qps, burst_sec)
    total_sec = pre_sec + burst_sec + post_sec
    burst_end_step = pre_sec + burst_sec
    
    rows = []
    pre_p99s = []
    
    for step in range(1, total_sec + 1):
        if step <= pre_sec:
            phase = 'pre_burst'
            target_qps = base_qps
        elif step <= burst_end_step:
            phase = 'burst'
            target_qps = burst_targets[step - pre_sec - 1]
        else:
            phase = 'post_burst'
            target_qps = base_qps
            
        lat = run_second(backend, cur, target_qps)
        lat.sort()
        p50 = pct(lat, 0.50)
        p95 = pct(lat, 0.95)
        p99 = pct(lat, 0.99)
        avg = statistics.mean(lat) if lat else 0.0
        
        if phase == 'pre_burst':
            pre_p99s.append(p99)
            
        row = {
            'second': step,
            'phase': phase,
            'shape': shape_type,
            'backend': backend_kind,
            'target_qps': target_qps,
            'actual_qps': len(lat),
            'avg_latency_ms': round(avg, 3),
            'p50_latency_ms': round(p50, 3),
            'p95_latency_ms': round(p95, 3),
            'p99_latency_ms': round(p99, 3),
            'max_latency_ms': round(max(lat), 3) if lat else 0.0,
            'hysteresis_H_t': 0.0
        }
        rows.append(row)
        print(f"sec={step:02d} phase={phase:10s} shape={shape_type:8s} target_qps={target_qps:3d} actual_qps={len(lat):3d} p99={p99:6.2f}ms")
        
    backend.close()
    
    base_p99_mean = round(statistics.mean(pre_p99s), 3) if pre_p99s else 1.0
    rec_threshold = round(base_p99_mean * 1.5, 3)
    
    recovery_time_s = None
    consecutive_ok = 0
    for row in rows:
        if row['second'] <= burst_end_step:
            continue
        if row['p99_latency_ms'] <= rec_threshold:
            consecutive_ok += 1
            if consecutive_ok >= RECOVERY_HOLD_SEC:
                recovery_time_s = (row['second'] - RECOVERY_HOLD_SEC + 1) - burst_end_step
                break
        else:
            consecutive_ok = 0
    if recovery_time_s is None:
        recovery_time_s = post_sec
        
    peak_burst_p99 = max(r['p99_latency_ms'] for r in rows if r['phase'] == 'burst')
    peak_target_qps = max(r['target_qps'] for r in rows if r['phase'] == 'burst')
    
    delta_load_pct = (peak_target_qps - base_qps) / max(base_qps, 1)
    delta_p99_pct = (peak_burst_p99 - base_p99_mean) / max(base_p99_mean, 0.001)
    baf = round(delta_p99_pct / max(delta_load_pct, 0.001), 2)
    
    post_rows = [r for r in rows if r['phase'] == 'post_burst']
    for idx, r in enumerate(post_rows, 1):
        h_t = round((r['p99_latency_ms'] - base_p99_mean) / base_p99_mean, 3)
        r['hysteresis_H_t'] = h_t
        
    auc_h = round(sum(max(0.0, r.get('hysteresis_H_t', 0.0)) for r in post_rows), 3)
    h_at_5s = post_rows[min(4, len(post_rows)-1)].get('hysteresis_H_t', 0.0) if post_rows else 0.0
    
    summary = {
        'backend': backend_kind,
        'shape': shape_type,
        'base_p99_ms': base_p99_mean,
        'peak_p99_ms': peak_burst_p99,
        'recovery_threshold_ms': rec_threshold,
        'recovery_time_s': recovery_time_s,
        'burst_amplification_factor_BAF': baf,
        'hysteresis_at_5s': h_at_5s,
        'cumulative_hysteresis_AUC_H': auc_h,
        'total_extra_workload_requests': 3600
    }
    
    ts_csv = os.path.join(RESULTS_DIR, f"timeseries_{backend_kind}_{shape_type}.csv")
    with open(ts_csv, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
        
    sum_csv = os.path.join(RESULTS_DIR, "summary_novelty_metrics.csv")
    file_exists = os.path.exists(sum_csv)
    with open(sum_csv, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(summary.keys()))
        if not file_exists:
            writer.writeheader()
        writer.writerow(summary)
        
    print(f"Summary [{backend_kind} - {shape_type}]: {summary}")
    return summary, rows

if __name__ == '__main__':
    backend = sys.argv[1] if len(sys.argv) > 1 else 'postgres_managed'
    for shape in ['sudden', 'ramp', 'repeated']:
        run_shape_experiment(backend, shape, base_qps=150, pre_sec=4, burst_sec=8, post_sec=8)
