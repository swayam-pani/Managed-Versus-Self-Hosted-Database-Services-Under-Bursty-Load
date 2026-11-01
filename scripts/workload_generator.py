"""
workload_generator.py
=====================
Core High-Performance Benchmark Workload Generator Engine
Course: Cloud Computing (CSE4001 / Sem 7) | P8: Managed vs Self-Hosted DBs Under Bursty Load

Key Architectural Highlights:
  1. Concurrency: Multi-threaded worker pool (ThreadPoolExecutor) simulating concurrent client connections.
  2. Nanosecond Precision: High-resolution timestamping via time.perf_counter_ns() preventing timer distortion.
  3. Statistical Rigor: Exact tail latency percentiles computed via numpy.percentile(latencies, [50, 95, 99]).
"""

import os
import sys
import time
import random
import argparse
import threading
import concurrent.futures
import numpy as np

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, CURRENT_DIR)

from db_backend import Backend


class WorkloadGenerator:
    """
    Simulates concurrent client sessions executing OLTP transactions with high-precision
    telemetry and statistical percentile calculation.
    """

    def __init__(self, backend_kind="postgres_managed", concurrency=10, read_ratio=0.75):
        self.backend_kind = backend_kind
        self.concurrency = concurrency
        self.read_ratio = read_ratio
        self.backend = Backend(backend_kind, max_connections=concurrency * 2)
        self.backend.ensure_schema_and_seed(n_accounts=10000)
        self._thread_local = threading.local()

    def _get_worker_connection_cursor(self):
        """Thread-safe connection and cursor allocator for worker threads."""
        if not hasattr(self._thread_local, "backend"):
            self._thread_local.backend = Backend(self.backend_kind, max_connections=4)
            self._thread_local.cur = self._thread_local.backend.cursor()
        return self._thread_local.backend, self._thread_local.cur

    # -------------------------------------------------------------------------
    # High-Precision Transaction Worker (Nanosecond Timer Measurement)
    # -------------------------------------------------------------------------
    def execute_transaction_worker(self):
        """
        Executes a single OLTP query (75% Read / 25% Write) and captures round-trip latency
        using time.perf_counter_ns() for sub-microsecond precision.
        """
        backend, cur = self._get_worker_connection_cursor()
        acc_id = random.randint(1, 10000)

        # High-precision start timestamp (Nanoseconds)
        t0_ns = time.perf_counter_ns()

        if random.random() < self.read_ratio:
            cur.execute(backend.q("SELECT balance, customer_name FROM accounts WHERE id = ?"), (acc_id,))
            cur.fetchone()
        else:
            amt = round(random.uniform(1.0, 25.0), 2)
            cur.execute(backend.q("UPDATE accounts SET balance = balance + ? WHERE id = ?"), (amt, acc_id))
            backend.commit()

        # High-precision end timestamp (Nanoseconds)
        t1_ns = time.perf_counter_ns()

        # Convert nanoseconds to milliseconds
        latency_ms = (t1_ns - t0_ns) / 1_000_000.0
        return latency_ms

    # -------------------------------------------------------------------------
    # Multi-Threaded Concurrent Worker Pool Loop
    # -------------------------------------------------------------------------
    def run_concurrent_second(self, target_qps):
        """
        Dispatches requests across a multi-threaded worker pool simulating concurrent
        client sessions with closed-loop arrivals for ~1 wall-clock second.
        """
        interval_s = 1.0 / max(target_qps, 1)
        window_end = time.time() + 1.0
        latencies = []

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.concurrency) as executor:
            futures = []
            while time.time() < window_end:
                f = executor.submit(self.execute_transaction_worker)
                futures.append(f)
                time.sleep(interval_s)

            for f in concurrent.futures.as_completed(futures):
                try:
                    lat_ms = f.result()
                    latencies.append(lat_ms)
                except Exception as e:
                    pass

        return latencies

    # -------------------------------------------------------------------------
    # Statistical Percentile Computation (numpy.percentile)
    # -------------------------------------------------------------------------
    @staticmethod
    def compute_percentiles(latencies):
        """
        Computes accurate p50, p95, and p99 tail latency percentiles from raw samples
        using numpy.percentile.
        """
        if not latencies:
            return {"p50": 0.0, "p95": 0.0, "p99": 0.0, "mean": 0.0, "count": 0}

        lat_arr = np.array(latencies, dtype=float)
        p50, p95, p99 = np.percentile(lat_arr, [50, 95, 99])

        return {
            "p50": round(float(p50), 3),
            "p95": round(float(p95), 3),
            "p99": round(float(p99), 3),
            "mean": round(float(np.mean(lat_arr)), 3),
            "count": len(latencies)
        }

    def close(self):
        self.backend.close()


def run_benchmark_session(backend_kind="postgres_managed", qps=150, concurrency=10, duration_sec=5):
    print(f"\n[BENCHMARK ENGINE] Starting WorkloadGenerator on {backend_kind}")
    print(f"Concurrency Workers: {concurrency} | Target Rate: {qps} QPS | Duration: {duration_sec}s")

    gen = WorkloadGenerator(backend_kind=backend_kind, concurrency=concurrency)
    all_latencies = []

    for s in range(1, duration_sec + 1):
        lats = gen.run_concurrent_second(target_qps=qps)
        all_latencies.extend(lats)
        sec_stats = gen.compute_percentiles(lats)
        print(f"Sec {s:02d} | Achieved: {sec_stats['count']:<4} QPS | "
              f"p50: {sec_stats['p50']:6.2f} ms | p95: {sec_stats['p95']:6.2f} ms | p99: {sec_stats['p99']:6.2f} ms")

    summary = gen.compute_percentiles(all_latencies)
    print("\n" + "=" * 60)
    print("SESSION TAIL LATENCY SUMMARY (numpy.percentile)")
    print(f"  • Total Requests Completed: {summary['count']}")
    print(f"  • Mean Latency:             {summary['mean']} ms")
    print(f"  • Median (p50):             {summary['p50']} ms")
    print(f"  • Tail Latency (p95):       {summary['p95']} ms")
    print(f"  • Critical Tail (p99):      {summary['p99']} ms")
    print("=" * 60 + "\n")

    gen.close()
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Multi-Threaded High-Precision Workload Generator")
    parser.add_argument("--backend", default="postgres_managed", choices=["postgres_managed", "sqlite", "postgres_docker"])
    parser.add_argument("--qps", type=int, default=100)
    parser.add_argument("--concurrency", type=int, default=8)
    parser.add_argument("--duration", type=int, default=5)
    args = parser.parse_args()

    run_benchmark_session(
        backend_kind=args.backend,
        qps=args.qps,
        concurrency=args.concurrency,
        duration_sec=args.duration
    )
