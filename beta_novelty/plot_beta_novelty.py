import os
import csv
import statistics
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_DIR = os.path.join(CURRENT_DIR, "results")
FIG_DIR = os.path.join(RESULTS_DIR, "figures")
os.makedirs(FIG_DIR, exist_ok=True)

def read_csv(path):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def plot_shape_sensitivity(backend="postgres_managed"):
    sudden_file = os.path.join(RESULTS_DIR, f"timeseries_{backend}_sudden.csv")
    ramp_file = os.path.join(RESULTS_DIR, f"timeseries_{backend}_ramp.csv")
    repeated_file = os.path.join(RESULTS_DIR, f"timeseries_{backend}_repeated.csv")
    
    s_rows = read_csv(sudden_file)
    r_rows = read_csv(ramp_file)
    rep_rows = read_csv(repeated_file)
    
    if not (s_rows and r_rows and rep_rows):
        print(f"Skipping plot_shape_sensitivity for {backend}: missing CSV files")
        return
        
    sec_s = [int(r["second"]) for r in s_rows]
    qps_s = [int(r["target_qps"]) for r in s_rows]
    p99_s = [float(r["p99_latency_ms"]) for r in s_rows]
    
    sec_r = [int(r["second"]) for r in r_rows]
    qps_r = [int(r["target_qps"]) for r in r_rows]
    p99_r = [float(r["p99_latency_ms"]) for r in r_rows]
    
    sec_rep = [int(r["second"]) for r in rep_rows]
    qps_rep = [int(r["target_qps"]) for r in rep_rows]
    p99_rep = [float(r["p99_latency_ms"]) for r in rep_rows]
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 8), sharex=True)
    
    # Subplot 1: Input Workload Arrival Profiles (Iso-Workload = Identical Area)
    ax1.plot(sec_s, qps_s, color="#DC2626", linewidth=2.2, label="Sudden Step (Plateau: +300 QPS)")
    ax1.plot(sec_r, qps_r, color="#2563EB", linewidth=2.2, linestyle="--", label="Gradual Ramp (Triangular Peak: +550 QPS)")
    ax1.plot(sec_rep, qps_rep, color="#059669", linewidth=2.2, linestyle="-.", label="Repeated Pulse (Dual Shock: +450 QPS)")
    ax1.set_ylabel("Arrival Rate (QPS)", fontsize=11, fontweight="bold")
    ax1.set_title(f"Iso-Workload Burst Shape Sensitivity Analysis [{backend}]\n(Identical Total Extra Requests = 3600)", fontsize=13, fontweight="bold", color="#1E3A8A")
    ax1.grid(True, linestyle="--", alpha=0.5)
    ax1.legend(loc="upper right", frameon=True)
    
    # Subplot 2: Resulting p99 Tail Latency
    ax2.plot(sec_s, p99_s, color="#DC2626", linewidth=2.2, marker="o", markersize=3, label="Sudden Burst p99 Response")
    ax2.plot(sec_r, p99_r, color="#2563EB", linewidth=2.2, linestyle="--", marker="s", markersize=3, label="Gradual Ramp p99 Response")
    ax2.plot(sec_rep, p99_rep, color="#059669", linewidth=2.2, linestyle="-.", marker="^", markersize=3, label="Repeated Pulse p99 Response")
    ax2.set_xlabel("Elapsed Time (Seconds)", fontsize=11, fontweight="bold")
    ax2.set_ylabel("Tail Latency p99 (ms)", fontsize=11, fontweight="bold")
    ax2.grid(True, linestyle="--", alpha=0.5)
    ax2.legend(loc="upper right", frameon=True)
    
    plt.tight_layout()
    out = os.path.join(FIG_DIR, f"shape_sensitivity_comparison_{backend}.png")
    plt.savefig(out, dpi=200)
    plt.close()
    print("Wrote", out)

def plot_hysteresis(backend="postgres_managed"):
    shapes = ["sudden", "ramp", "repeated"]
    colors = {"sudden": "#DC2626", "ramp": "#2563EB", "repeated": "#059669"}
    
    plt.figure(figsize=(9, 5))
    has_data = False
    
    for sh in shapes:
        path = os.path.join(RESULTS_DIR, f"timeseries_{backend}_{sh}.csv")
        rows = read_csv(path)
        if not rows:
            continue
        has_data = True
        post_rows = [r for r in rows if r["phase"] == "post_burst"]
        if not post_rows:
            continue
        base_p99 = statistics.mean([float(r["p99_latency_ms"]) for r in rows if r["phase"] == "pre_burst"])
        
        t_post = [idx for idx in range(1, len(post_rows) + 1)]
        h_vals = [round((float(r["p99_latency_ms"]) - base_p99) / base_p99, 3) for r in post_rows]
        
        plt.plot(t_post, h_vals, color=colors[sh], linewidth=2.2, marker="o", markersize=4,
                 label=f"{sh.capitalize()} Shape (AUC_H = {sum(max(0, h) for h in h_vals):.2f})")
                 
    if not has_data:
        print(f"Skipping plot_hysteresis for {backend}: no data")
        return
        
    plt.axhline(0.0, color="gray", linestyle=":", label="Baseline Equivalence (H = 0)")
    plt.axhline(0.5, color="orange", linestyle="--", alpha=0.7, label="1.5x Recovery Threshold (H = 0.5)")
    plt.title(f"Post-Burst Performance Hysteresis Decay Curve H(t) [{backend}]\n[H(t) = (p99(t) - p99_base) / p99_base]", fontsize=12, fontweight="bold", color="#1E3A8A")
    plt.xlabel("Seconds Elapsed After Burst Ended", fontsize=11, fontweight="bold")
    plt.ylabel("Relative Hysteresis Index H(t)", fontsize=11, fontweight="bold")
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.legend(frameon=True)
    plt.tight_layout()
    out = os.path.join(FIG_DIR, f"performance_hysteresis_decay_{backend}.png")
    plt.savefig(out, dpi=200)
    plt.close()
    print("Wrote", out)

def plot_joint_novelty_summary():
    summary_path = os.path.join(RESULTS_DIR, "summary_novelty_metrics.csv")
    rows = read_csv(summary_path)
    if not rows:
        return
    
    import numpy as np
    shapes = ["sudden", "ramp", "repeated"]
    shape_labels = ["Sudden Step", "Gradual Ramp", "Repeated Pulse"]
    
    managed_auc = [float(next(r["cumulative_hysteresis_AUC_H"] for r in rows if r["backend"]=="postgres_managed" and r["shape"]==s)) for s in shapes]
    sqlite_auc = [float(next(r["cumulative_hysteresis_AUC_H"] for r in rows if r["backend"]=="sqlite" and r["shape"]==s)) for s in shapes]
    
    managed_baf = [float(next(r["burst_amplification_factor_BAF"] for r in rows if r["backend"]=="postgres_managed" and r["shape"]==s)) for s in shapes]
    sqlite_baf = [float(next(r["burst_amplification_factor_BAF"] for r in rows if r["backend"]=="sqlite" and r["shape"]==s)) for s in shapes]
    
    x = np.arange(len(shapes))
    width = 0.35
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))
    
    rects1 = ax1.bar(x - width/2, sqlite_auc, width, label='Self-Hosted Baseline (SQLite)', color='#64748B', edgecolor='#334155')
    rects2 = ax1.bar(x + width/2, managed_auc, width, label='Managed Cloud (AWS Neon)', color='#2563EB', edgecolor='#1D4ED8')
    ax1.set_ylabel('Hysteresis Area Under Curve ($AUC_H$)', fontweight='bold')
    ax1.set_title('Cumulative Performance Hysteresis by Burst Shape\n(Iso-Workload = 3600 Extra Requests)', fontweight='bold', color='#1E3A8A')
    ax1.set_xticks(x)
    ax1.set_xticklabels(shape_labels, fontweight='bold')
    ax1.legend(frameon=True)
    ax1.grid(True, linestyle='--', alpha=0.4, axis='y')
    
    for r in rects1:
        h = r.get_height()
        ax1.annotate(f'{h:.2f}', xy=(r.get_x() + r.get_width() / 2, h), xytext=(0, 3),
                     textcoords="offset points", ha='center', va='bottom', fontsize=9, fontweight='bold')
    for r in rects2:
        h = r.get_height()
        ax1.annotate(f'{h:.3f}', xy=(r.get_x() + r.get_width() / 2, h), xytext=(0, 3),
                     textcoords="offset points", ha='center', va='bottom', fontsize=9, fontweight='bold')
                     
    rects3 = ax2.bar(x - width/2, sqlite_baf, width, label='Self-Hosted Baseline (SQLite)', color='#64748B', edgecolor='#334155')
    rects4 = ax2.bar(x + width/2, managed_baf, width, label='Managed Cloud (AWS Neon)', color='#2563EB', edgecolor='#1D4ED8')
    ax2.set_ylabel('Burst Amplification Factor (BAF)', fontweight='bold')
    ax2.set_title('Sensitivity to Burst Shape: BAF = (%$\\Delta p_{99}$) / (%$\\Delta Load$)', fontweight='bold', color='#1E3A8A')
    ax2.set_xticks(x)
    ax2.set_xticklabels(shape_labels, fontweight='bold')
    ax2.legend(frameon=True)
    ax2.grid(True, linestyle='--', alpha=0.4, axis='y')
    
    for r in rects3:
        h = r.get_height()
        ax2.annotate(f'{h:.2f}', xy=(r.get_x() + r.get_width() / 2, h), xytext=(0, 3),
                     textcoords="offset points", ha='center', va='bottom', fontsize=9, fontweight='bold')
    for r in rects4:
        h = r.get_height()
        ax2.annotate(f'{h:.2f}', xy=(r.get_x() + r.get_width() / 2, h), xytext=(0, 3),
                     textcoords="offset points", ha='center', va='bottom', fontsize=9, fontweight='bold')
                     
    plt.tight_layout()
    out = os.path.join(FIG_DIR, "novelty_hysteresis_and_baf_comparison.png")
    plt.savefig(out, dpi=200)
    plt.close()
    print("Wrote", out)

if __name__ == "__main__":
    for b in ["postgres_managed", "sqlite", "postgres_self_hosted"]:
        plot_shape_sensitivity(b)
        plot_hysteresis(b)
    plot_joint_novelty_summary()
