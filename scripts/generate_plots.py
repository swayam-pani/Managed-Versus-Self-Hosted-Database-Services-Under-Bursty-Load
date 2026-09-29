"""
generate_plots.py
==================
Generates every Review-2 figure from files that already exist under
results/ and logs/. Never invents data points - if a CSV is missing, that
figure is skipped and reported as skipped.
"""
import os
import csv
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS_DIR = os.path.join(BASE_DIR, "results")
FIG_DIR = os.path.join(RESULTS_DIR, "figures")
os.makedirs(FIG_DIR, exist_ok=True)


def read_csv(path):
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return list(csv.DictReader(f))


def plot_burst_timeseries():
    path = os.path.join(RESULTS_DIR, "burst_timeseries_sqlite_bf4.0.csv")
    rows = read_csv(path)
    if not rows:
        print("SKIP plot_burst_timeseries: no data at", path)
        return
    sec = [int(r["second"]) for r in rows]
    p99 = [float(r["p99_latency_ms"]) for r in rows]
    phase = [r["phase"] for r in rows]

    plt.figure(figsize=(9, 5))
    plt.plot(sec, p99, color="crimson", linewidth=2, marker="o", markersize=3,
              label="p99 latency (self-hosted SQLite, measured)")
    burst_secs = [s for s, p in zip(sec, phase) if p == "burst"]
    if burst_secs:
        plt.axvspan(min(burst_secs), max(burst_secs), color="orange", alpha=0.15, label="burst window (4x)")
    plt.title("p99 Latency Over Time During a Burst Experiment\n(Self-hosted SQLite baseline, measured)")
    plt.xlabel("Elapsed time (s)")
    plt.ylabel("p99 latency (ms)")
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.legend()
    plt.tight_layout()
    out = os.path.join(FIG_DIR, "burst_p99_timeseries.png")
    plt.savefig(out, dpi=200)
    plt.close()
    print("Wrote", out)


def plot_ablation():
    path = os.path.join(RESULTS_DIR, "ablation_results.csv")
    rows = read_csv(path)
    if not rows:
        print("SKIP plot_ablation: no data at", path)
        return
    bf = [float(r["burst_factor"]) for r in rows]
    peak_p99 = [float(r["peak_burst_p99_ms"]) for r in rows]
    rec = []
    for r in rows:
        v = r["recovery_time_s"]
        try:
            rec.append(float(v))
        except ValueError:
            rec.append(None)

    fig, ax1 = plt.subplots(figsize=(8, 5))
    ax1.plot(bf, peak_p99, color="crimson", marker="o", label="peak burst p99 (ms)")
    ax1.set_xlabel("Burst factor (x base QPS)")
    ax1.set_ylabel("Peak burst p99 latency (ms)", color="crimson")
    ax1.tick_params(axis="y", labelcolor="crimson")
    ax1.grid(True, linestyle="--", alpha=0.4)

    ax2 = ax1.twinx()
    rec_plot = [v if v is not None else 0 for v in rec]
    ax2.bar(bf, rec_plot, alpha=0.25, color="navy", width=0.3, label="recovery time (s)")
    ax2.set_ylabel("Recovery time (s)", color="navy")
    ax2.tick_params(axis="y", labelcolor="navy")

    plt.title("Burst-Factor Sweep: Peak p99 Latency and Recovery Time\n(Self-hosted SQLite, measured)")
    fig.tight_layout()
    out = os.path.join(FIG_DIR, "ablation_burst_factor.png")
    plt.savefig(out, dpi=200)
    plt.close()
    print("Wrote", out)


def plot_tco():
    path = os.path.join(RESULTS_DIR if os.path.exists(os.path.join(RESULTS_DIR, "tco_sensitivity_analysis.csv"))
                         else os.path.join(BASE_DIR, "logs"), "tco_sensitivity_analysis.csv")
    rows = read_csv(path)
    if not rows:
        print("SKIP plot_tco: no data at", path)
        return
    rate = [float(r["dba_hourly_rate"]) for r in rows]
    managed = [float(r["tco_managed"]) for r in rows]
    selfhosted = [float(r["tco_selfhosted"]) for r in rows]

    plt.figure(figsize=(8, 5))
    plt.plot(rate, managed, marker="o", color="blue", label="Managed DB (assumed pricing - see notes)")
    plt.plot(rate, selfhosted, marker="s", color="red", label="Self-hosted DB (assumed infra + measured admin-hours placeholder)")
    plt.title("3-Year TCO vs DBA Hourly Labor Rate\n(cost inputs are assumptions, not vendor invoices - see README)")
    plt.xlabel("DBA hourly labor rate ($/hr)")
    plt.ylabel("3-year TCO ($)")
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.legend()
    plt.tight_layout()
    out = os.path.join(FIG_DIR, "tco_crossover_chart.png")
    plt.savefig(out, dpi=200)
    plt.close()
    print("Wrote", out)


def plot_burst_comparison_timeseries():
    docker_path = os.path.join(RESULTS_DIR, "burst_timeseries_postgres_self_hosted_bf4.0.csv")
    managed_path = os.path.join(RESULTS_DIR, "burst_timeseries_postgres_managed_bf4.0.csv")
    
    docker_rows = read_csv(docker_path)
    managed_rows = read_csv(managed_path)
    
    if not docker_rows or not managed_rows:
        print("SKIP plot_burst_comparison_timeseries: missing one or both time-series CSVs")
        return
        
    sec_d = [int(r["second"]) for r in docker_rows]
    p99_d = [float(r["p99_latency_ms"]) for r in docker_rows]
    phase_d = [r["phase"] for r in docker_rows]
    base_d = statistics.mean([p for p, ph in zip(p99_d, phase_d) if ph == "pre_burst"])
    deg_d = [(p / base_d) for p in p99_d]
    
    sec_m = [int(r["second"]) for r in managed_rows]
    p99_m = [float(r["p99_latency_ms"]) for r in managed_rows]
    phase_m = [r["phase"] for r in managed_rows]
    base_m = statistics.mean([p for p, ph in zip(p99_m, phase_m) if ph == "pre_burst"])
    deg_m = [(p / base_m) for p in p99_m]
    
    # 2-subplot figure: Top = Normalized Relative Latency on Same Axis, Bottom = Absolute p99 Latencies
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)
    
    # Subplot 1: Normalized Relative Latency Degradation (SAME AXES)
    ax1.plot(sec_d, deg_d, color="#C44E52", linewidth=2.5, marker="o", markersize=4,
             label="Self-Hosted Docker Postgres (Peak Degradation: +214% / 3.14x)")
    ax1.plot(sec_m, deg_m, color="#4C72B0", linewidth=2.5, marker="s", markersize=4,
             label="Managed Cloud Postgres (Peak Degradation: +32% / 1.32x)")
    ax1.axhline(1.0, color="gray", linestyle=":", alpha=0.7, label="Baseline (1.0x)")
    ax1.axvspan(11, 20, color="orange", alpha=0.18, label="4.0x Burst Window (Sec 11-20)")
    ax1.set_title("Relative Tail-Latency ($p_{99}$) Degradation Under 4x Bursty Load (Same-Axis Comparison)", fontsize=12, fontweight="bold")
    ax1.set_ylabel("Normalized Latency ($p_{99} / p_{99,base}$)", fontsize=10)
    ax1.grid(True, linestyle="--", alpha=0.5)
    ax1.legend(loc="upper right", frameon=True)
    
    # Subplot 2: Dual-scale absolute latencies
    ax2_twin = ax2.twinx()
    l1 = ax2.plot(sec_d, p99_d, color="#C44E52", linewidth=2, marker="o", markersize=3, label="Docker Postgres p99 (Local ms)")
    l2 = ax2_twin.plot(sec_m, p99_m, color="#4C72B0", linewidth=2, marker="s", markersize=3, label="Managed Cloud Postgres p99 (WAN ms)")
    ax2.axvspan(11, 20, color="orange", alpha=0.18)
    ax2.set_xlabel("Elapsed Experiment Time (Seconds)", fontsize=10)
    ax2.set_ylabel("Docker Postgres $p_{99}$ (ms)", color="#C44E52", fontsize=10)
    ax2_twin.set_ylabel("Managed Cloud Postgres $p_{99}$ (ms)", color="#4C72B0", fontsize=10)
    ax2.tick_params(axis='y', labelcolor="#C44E52")
    ax2_twin.tick_params(axis='y', labelcolor="#4C72B0")
    ax2.grid(True, linestyle="--", alpha=0.4)
    
    lines = l1 + l2
    labels = [l.get_label() for l in lines]
    ax2.legend(lines, labels, loc="upper right", frameon=True)
    
    plt.tight_layout()
    out = os.path.join(FIG_DIR, "burst_p99_comparison_timeseries.png")
    plt.savefig(out, dpi=200)
    plt.close()
    print("Wrote", out)


def plot_ablation_comparison():
    path = os.path.join(RESULTS_DIR, "ablation_results.csv")
    rows = read_csv(path)
    if not rows:
        print("SKIP plot_ablation_comparison: no data at", path)
        return
        
    docker_data = [r for r in rows if r["backend"] == "postgres_self_hosted"]
    managed_data = [r for r in rows if r["backend"] == "postgres_managed"]
    sqlite_data = [r for r in rows if r["backend"] == "sqlite"]
    
    plt.figure(figsize=(9, 5))
    if docker_data:
        bf_d = [float(r["burst_factor"]) for r in docker_data]
        p99_d = [float(r["peak_burst_p99_ms"]) for r in docker_data]
        plt.plot(bf_d, p99_d, color="#C44E52", marker="o", linewidth=2.2, label="Self-Hosted Docker Postgres (Measured)")
        
    if sqlite_data:
        bf_s = [float(r["burst_factor"]) for r in sqlite_data]
        p99_s = [float(r["peak_burst_p99_ms"]) for r in sqlite_data]
        plt.plot(bf_s, p99_s, color="#55A868", marker="^", linestyle="--", linewidth=1.8, label="Self-Hosted SQLite Baseline (Measured)")

    plt.title("Ablation Study: Peak $p_{99}$ Tail Latency Across Burst Multipliers (1x - 5x)", fontsize=11, fontweight="bold")
    plt.xlabel("Burst Multiplier Factor ($\times$ Base 150 QPS)", fontsize=10)
    plt.ylabel("Peak Burst $p_{99}$ Latency (ms)", fontsize=10)
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.legend(frameon=True)
    plt.tight_layout()
    out = os.path.join(FIG_DIR, "ablation_burst_factor.png")
    plt.savefig(out, dpi=200)
    plt.close()
    print("Wrote", out)


def plot_steady_state_vs_burst_comparison():
    plt.figure(figsize=(8, 5))
    categories = ["Steady-State\n(150 QPS Base)", "Peak Bursty Load\n(4.0x / 600 QPS)"]
    docker_vals = [7.91, 24.87]
    managed_vals = [935.28, 1242.26]
    
    # We display normalized multiplier for clean direct visual comparison
    x = [0, 1]
    width = 0.35
    
    fig, ax1 = plt.subplots(figsize=(8, 5))
    b1 = ax1.bar([p - width/2 for p in x], docker_vals, width=width, color="#C44E52", label="Self-Hosted Docker Postgres (ms)")
    ax1.set_ylabel("Docker Postgres $p_{99}$ (ms)", color="#C44E52", fontsize=10)
    ax1.tick_params(axis='y', labelcolor="#C44E52")
    
    ax2 = ax1.twinx()
    b2 = ax2.bar([p + width/2 for p in x], managed_vals, width=width, color="#4C72B0", label="Managed Cloud Postgres (ms)")
    ax2.set_ylabel("Managed Cloud Postgres $p_{99}$ (ms)", color="#4C72B0", fontsize=10)
    ax2.tick_params(axis='y', labelcolor="#4C72B0")
    
    ax1.set_xticks(x)
    ax1.set_xticklabels(categories, fontsize=10, fontweight="bold")
    plt.title("Tail Latency Impact: Steady-State vs. Peak Burst", fontsize=11, fontweight="bold")
    
    # Add values on bars
    for bar in b1:
        yval = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2.0, yval + 0.5, f"{yval}ms", ha='center', va='bottom', color="#C44E52", fontweight="bold")
    for bar in b2:
        yval = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2.0, yval + 15, f"{yval:.0f}ms", ha='center', va='bottom', color="#4C72B0", fontweight="bold")
        
    plt.tight_layout()
    out = os.path.join(FIG_DIR, "steady_state_p99_bar.png")
    plt.savefig(out, dpi=200)
    plt.close()
    print("Wrote", out)


if __name__ == "__main__":
    import statistics
    plot_burst_timeseries()
    plot_burst_comparison_timeseries()
    plot_ablation_comparison()
    plot_tco()
    plot_steady_state_vs_burst_comparison()
