import os
import sys
import time
import csv
import statistics

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(CURRENT_DIR)
SCRIPTS_DIR = os.path.join(PROJECT_DIR, 'scripts')
sys.path.insert(0, SCRIPTS_DIR)

from db_backend import Backend
from harness_burst_shapes import run_second, pct

RESULTS_DIR = os.path.join(CURRENT_DIR, 'results')
os.makedirs(RESULTS_DIR, exist_ok=True)

def evaluate_slo_breaking_point(backend_kind, slo_threshold_ms, multipliers=None):
    if multipliers is None:
        multipliers = [1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0]
        
    print(f"\n=======================================================")
    print(f"SLO BREAKING POINT EVALUATION: {backend_kind}")
    print(f"Target SLO: p99 < {slo_threshold_ms:.1f} ms")
    print(f"=======================================================")
    
    backend = Backend(backend_kind)
    backend.ensure_schema_and_seed()
    cur = backend.cursor()
    
    base_qps = 150
    results = []
    breaking_point = None
    
    for mult in multipliers:
        # 3s pre-burst, 4s burst, 4s post-burst
        pre_p99s = []
        for _ in range(3):
            lat = run_second(backend, cur, base_qps)
            lat.sort()
            pre_p99s.append(pct(lat, 0.99))
            
        base_p99 = statistics.mean(pre_p99s) if pre_p99s else 1.0
        target_burst_qps = int(base_qps * mult)
        
        burst_p99s = []
        for _ in range(4):
            lat = run_second(backend, cur, target_burst_qps)
            lat.sort()
            burst_p99s.append(pct(lat, 0.99))
            
        peak_p99 = max(burst_p99s) if burst_p99s else base_p99
        status = "PASS" if peak_p99 <= slo_threshold_ms else "FAIL"
        
        delta_load_pct = (target_burst_qps - base_qps) / max(base_qps, 1)
        delta_p99_pct = (peak_p99 - base_p99) / max(base_p99, 0.001)
        baf = round(delta_p99_pct / max(delta_load_pct, 0.001), 2)
        
        row = {
            'backend': backend_kind,
            'multiplier': mult,
            'target_qps': target_burst_qps,
            'base_p99_ms': round(base_p99, 2),
            'peak_p99_ms': round(peak_p99, 2),
            'slo_threshold_ms': slo_threshold_ms,
            'status': status,
            'BAF': baf
        }
        results.append(row)
        print(f"Multiplier {mult:3.1f}x ({target_burst_qps:4d} QPS) -> Peak p99: {peak_p99:6.2f} ms | SLO: {status} | BAF: {baf}")
        
        if status == "FAIL" and breaking_point is None:
            breaking_point = mult
            
    backend.close()
    
    b_slo = max([r['multiplier'] for r in results if r['status'] == 'PASS'], default=0.0)
    print(f"\n===> RESULT: Empirical Burst SLO Capacity (B_SLO) for {backend_kind} = {b_slo}x")
    if breaking_point:
        print(f"===> RESULT: Breaking Point Occurred at {breaking_point}x Multiplier")
    else:
        print(f"===> RESULT: No breaking point reached up to {max(multipliers)}x")
        
    out_csv = os.path.join(RESULTS_DIR, f"slo_breaking_point_{backend_kind}.csv")
    with open(out_csv, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(results[0].keys()))
        writer.writeheader()
        writer.writerows(results)
    print(f"Saved SLO breaking point data to {out_csv}")
    return b_slo, results

if __name__ == '__main__':
    backend = sys.argv[1] if len(sys.argv) > 1 else 'postgres_managed'
    slo = float(sys.argv[2]) if len(sys.argv) > 2 else 1150.0
    evaluate_slo_breaking_point(backend, slo)
