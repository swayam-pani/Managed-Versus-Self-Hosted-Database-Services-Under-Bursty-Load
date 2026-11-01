"""
generate_review3_statistical_plots.py
=====================================
Generates publication-quality figures with statistical error bars and variance envelopes
for Review 3, adhering strictly to the rubric:
"Statistical soundness: Error bars or confidence intervals. A bar chart from a single run scores 0 here."

Outputs generated in results/figures/:
1. review3_statistical_bar_with_errorbars.png
2. review3_timeseries_variance_envelope.png
3. review3_workload_sensitivity_comparison.png
"""
import os
import csv
import math
import statistics
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(CURRENT_DIR)
RESULTS_DIR = os.path.join(PROJECT_DIR, "results")
FIG_DIR = os.path.join(RESULTS_DIR, "figures")
os.makedirs(FIG_DIR, exist_ok=True)

def read_csv(path):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def plot_statistical_bar_charts(backend="postgres_managed"):
    stat_file = os.path.join(RESULTS_DIR, f"review3_statistical_summary_{backend}.csv")
    rows = read_csv(stat_file)
    if not rows:
        print(f"No statistical summary file found for {backend} at {stat_file}")
        return
        
    workloads = ["read_heavy", "balanced", "write_heavy"]
    workload_labels = ["Read-Heavy (80/20)", "Balanced (50/50)", "Write-Heavy (20/80)"]
    
    # Extract Means and 95% Confidence Intervals
    base_means = []
    base_cis = []
    peak_means = []
    peak_cis = []
    recov_means = []
    recov_cis = []
    
    for wl in workloads:
        match = next((r for r in rows if r["workload"] == wl), None)
        if match:
            base_means.append(float(match["base_p99_mean_ms"]))
            base_cis.append(float(match["base_p99_ci95"]))
            peak_means.append(float(match["peak_p99_mean_ms"]))
            peak_cis.append(float(match["peak_p99_ci95"]))
            recov_means.append(float(match["recovery_time_mean_s"]))
            recov_cis.append(float(match["recovery_time_ci95"]))
        else:
            base_means.append(0); base_cis.append(0)
            peak_means.append(0); peak_cis.append(0)
            recov_means.append(0); recov_cis.append(0)
            
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5))
    
    x = np.arange(len(workloads))
    width = 0.35
    
    # Panel 1: p99 Latency with 95% Confidence Interval Error Bars
    rects1 = ax1.bar(x - width/2, base_means, width, yerr=base_cis, capsize=6,
                     label='Baseline p99 (150 QPS)', color='#93C5FD', edgecolor='#1D4ED8', error_kw={'elinewidth': 1.8, 'ecolor': '#1E3A8A'})
    rects2 = ax1.bar(x + width/2, peak_means, width, yerr=peak_cis, capsize=6,
                     label='Peak Burst p99 (600 QPS)', color='#2563EB', edgecolor='#1E3A8A', error_kw={'elinewidth': 1.8, 'ecolor': '#B91C1C'})
                     
    ax1.set_ylabel('p99 Tail Latency (ms)', fontsize=11, fontweight='bold')
    ax1.set_title(f'p99 Tail Latency by Workload [Mean $\\pm$ 95% CI]\n(Backend: {backend} | N=3 Independent Trials)',
                  fontsize=12, fontweight='bold', color='#1E3A8A')
    ax1.set_xticks(x)
    ax1.set_xticklabels(workload_labels, fontsize=10, fontweight='bold')
    ax1.legend(frameon=True, loc='upper left')
    ax1.grid(True, linestyle='--', alpha=0.4, axis='y')
    
    for r, m, ci in zip(rects1, base_means, base_cis):
        ax1.annotate(f'{m:.1f}\n(±{ci:.1f})', xy=(r.get_x() + r.get_width()/2, m), xytext=(0, 10),
                     textcoords="offset points", ha='center', va='bottom', fontsize=8, fontweight='bold')
    for r, m, ci in zip(rects2, peak_means, peak_cis):
        ax1.annotate(f'{m:.1f}\n(±{ci:.1f})', xy=(r.get_x() + r.get_width()/2, m), xytext=(0, 10),
                     textcoords="offset points", ha='center', va='bottom', fontsize=8, fontweight='bold')
                     
    # Panel 2: Recovery Time with 95% Confidence Intervals
    rects3 = ax2.bar(x, recov_means, width*1.2, yerr=recov_cis, capsize=6,
                     label='Mean Recovery Time (s)', color='#10B981', edgecolor='#047857', error_kw={'elinewidth': 1.8, 'ecolor': '#064E3B'})
    ax2.set_ylabel('Empirical Recovery Time (Seconds)', fontsize=11, fontweight='bold')
    ax2.set_title(f'Post-Burst Recovery Time [Mean $\\pm$ 95% CI]\n(Time to remain $\\leq 1.5\\times$ baseline for 3s)',
                  fontsize=12, fontweight='bold', color='#1E3A8A')
    ax2.set_xticks(x)
    ax2.set_xticklabels(workload_labels, fontsize=10, fontweight='bold')
    ax2.legend(frameon=True, loc='upper right')
    ax2.grid(True, linestyle='--', alpha=0.4, axis='y')
    
    for r, m, ci in zip(rects3, recov_means, recov_cis):
        ax2.annotate(f'{m:.2f} s\n(±{ci:.2f})', xy=(r.get_x() + r.get_width()/2, m), xytext=(0, 10),
                     textcoords="offset points", ha='center', va='bottom', fontsize=8, fontweight='bold')
                     
    plt.tight_layout()
    out = os.path.join(FIG_DIR, f"review3_statistical_bar_with_errorbars_{backend}.png")
    plt.savefig(out, dpi=200)
    plt.close()
    print("Wrote", out)

def plot_timeseries_variance_envelope(backend="postgres_managed"):
    ts_file = os.path.join(RESULTS_DIR, f"review3_timeseries_raw_{backend}.csv")
    rows = read_csv(ts_file)
    if not rows:
        print(f"No timeseries data found for {backend} at {ts_file}")
        return
        
    workloads = ["read_heavy", "balanced", "write_heavy"]
    colors = {"read_heavy": "#2563EB", "balanced": "#D97706", "write_heavy": "#DC2626"}
    labels = {"read_heavy": "Read-Heavy (80/20)", "balanced": "Balanced (50/50)", "write_heavy": "Write-Heavy (20/80)"}
    
    plt.figure(figsize=(12, 6.5))
    
    for wl in workloads:
        wl_rows = [r for r in rows if r["workload"] == wl]
        if not wl_rows:
            continue
        seconds = sorted(list(set(int(r["second"]) for r in wl_rows)))
        
        means = []
        stds = []
        for s in seconds:
            vals = [float(r["p99"]) for r in wl_rows if int(r["second"]) == s]
            m = statistics.mean(vals)
            sd = statistics.stdev(vals) if len(vals) > 1 else 0.0
            means.append(m)
            stds.append(sd)
            
        means = np.array(means)
        stds = np.array(stds)
        
        plt.plot(seconds, means, color=colors[wl], linewidth=2.2, label=f"{labels[wl]} Mean p99")
        plt.fill_between(seconds, np.maximum(0, means - stds), means + stds, color=colors[wl], alpha=0.18,
                         label=f"{labels[wl]} ($\\pm 1\\sigma$ Envelope)")
                         
    # Visual cues for phases
    plt.axvspan(1, 6, color='#F3F4F6', alpha=0.6, label='Phase 1: Baseline (150 QPS)')
    plt.axvspan(7, 16, color='#FEE2E2', alpha=0.5, label='Phase 2: 4x Shock Burst (600 QPS)')
    plt.axvspan(17, 30, color='#ECFDF5', alpha=0.5, label='Phase 3: Post-Burst Recovery')
    
    plt.title(f"Dynamic Latency Response with Empirical Variance Envelopes [$\\mu \\pm \\sigma$]\n(Backend: {backend} | N=3 Repeated Trials)",
              fontsize=13, fontweight='bold', color='#1E3A8A')
    plt.xlabel("Elapsed Timeline (Seconds)", fontsize=11, fontweight='bold')
    plt.ylabel("p99 Tail Latency (ms)", fontsize=11, fontweight='bold')
    plt.grid(True, linestyle='--', alpha=0.4)
    
    # Avoid duplicate legend handles
    handles, legend_labels = plt.gca().get_legend_handles_labels()
    by_label = dict(zip(legend_labels, handles))
    plt.legend(by_label.values(), by_label.keys(), loc='upper left', frameon=True, fontsize=9)
    
    plt.tight_layout()
    out = os.path.join(FIG_DIR, f"review3_timeseries_variance_envelope_{backend}.png")
    plt.savefig(out, dpi=200)
    plt.close()
    print("Wrote", out)

def plot_combined_workload_comparison():
    managed_file = os.path.join(RESULTS_DIR, "review3_statistical_summary_postgres_managed.csv")
    sqlite_file = os.path.join(RESULTS_DIR, "review3_statistical_summary_sqlite.csv")
    
    m_rows = read_csv(managed_file)
    s_rows = read_csv(sqlite_file)
    
    if not (m_rows and s_rows):
        print("Skipping combined comparison: waiting for both summaries.")
        return
        
    workloads = ["read_heavy", "balanced", "write_heavy"]
    workload_labels = ["Read-Heavy (80/20)", "Balanced (50/50)", "Write-Heavy (20/80)"]
    
    # BAF comparison
    m_baf = [float(next(r["baf_mean"] for r in m_rows if r["workload"]==w)) for w in workloads]
    m_baf_ci = [float(next(r["baf_ci95"] for r in m_rows if r["workload"]==w)) for w in workloads]
    s_baf = [float(next(r["baf_mean"] for r in s_rows if r["workload"]==w)) for w in workloads]
    s_baf_ci = [float(next(r["baf_ci95"] for r in s_rows if r["workload"]==w)) for w in workloads]
    
    # Recovery Time comparison
    m_rec = [float(next(r["recovery_time_mean_s"] for r in m_rows if r["workload"]==w)) for w in workloads]
    m_rec_ci = [float(next(r["recovery_time_ci95"] for r in m_rows if r["workload"]==w)) for w in workloads]
    s_rec = [float(next(r["recovery_time_mean_s"] for r in s_rows if r["workload"]==w)) for w in workloads]
    s_rec_ci = [float(next(r["recovery_time_ci95"] for r in s_rows if r["workload"]==w)) for w in workloads]
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5))
    x = np.arange(len(workloads))
    width = 0.35
    
    # Panel 1: Burst Amplification Factor
    rects1 = ax1.bar(x - width/2, s_baf, width, yerr=s_baf_ci, capsize=6,
                     label='Self-Hosted Baseline (SQLite)', color='#64748B', edgecolor='#334155', error_kw={'elinewidth': 1.8, 'ecolor': '#0F172A'})
    rects2 = ax1.bar(x + width/2, m_baf, width, yerr=m_baf_ci, capsize=6,
                     label='Managed Cloud (AWS Neon)', color='#2563EB', edgecolor='#1D4ED8', error_kw={'elinewidth': 1.8, 'ecolor': '#1E3A8A'})
    ax1.set_ylabel('Burst Amplification Factor (BAF) [Mean $\\pm$ 95% CI]', fontweight='bold')
    ax1.set_title('Burst Sensitivity by Workload [Mean $\\pm$ 95% CI]\nBAF = (%$\\Delta p_{99}$) / (%$\\Delta Load$)', fontweight='bold', color='#1E3A8A')
    ax1.set_xticks(x)
    ax1.set_xticklabels(workload_labels, fontweight='bold')
    ax1.legend(frameon=True)
    ax1.grid(True, linestyle='--', alpha=0.4, axis='y')
    
    # Panel 2: Recovery Time
    rects3 = ax2.bar(x - width/2, s_rec, width, yerr=s_rec_ci, capsize=6,
                     label='Self-Hosted Baseline (SQLite)', color='#64748B', edgecolor='#334155', error_kw={'elinewidth': 1.8, 'ecolor': '#0F172A'})
    rects4 = ax2.bar(x + width/2, m_rec, width, yerr=m_rec_ci, capsize=6,
                     label='Managed Cloud (AWS Neon)', color='#10B981', edgecolor='#047857', error_kw={'elinewidth': 1.8, 'ecolor': '#064E3B'})
    ax2.set_ylabel('Recovery Time (Seconds) [Mean $\\pm$ 95% CI]', fontweight='bold')
    ax2.set_title('Post-Burst Recovery Time Comparison [Mean $\\pm$ 95% CI]\n(Time to stabilize under $1.5\\times$ baseline for 3s)', fontweight='bold', color='#1E3A8A')
    ax2.set_xticks(x)
    ax2.set_xticklabels(workload_labels, fontweight='bold')
    ax2.legend(frameon=True)
    ax2.grid(True, linestyle='--', alpha=0.4, axis='y')
    
    plt.tight_layout()
    out = os.path.join(FIG_DIR, "review3_workload_sensitivity_comparison.png")
    plt.savefig(out, dpi=200)
    plt.close()
    print("Wrote", out)

if __name__ == "__main__":
    for b in ["postgres_managed", "sqlite"]:
        plot_statistical_bar_charts(b)
        plot_timeseries_variance_envelope(b)
    plot_combined_workload_comparison()
