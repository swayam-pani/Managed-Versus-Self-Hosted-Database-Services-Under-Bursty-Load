import os
import matplotlib.pyplot as plt
import numpy as np

# Styling configuration
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['font.size'] = 10

out_dir = r"beta_novelty\results\figures"
os.makedirs(out_dir, exist_ok=True)
out_file = os.path.join(out_dir, "novelty_docker_vs_neon_comparison.png")

# Data from empirical benchmark runs (Iso-Workload = 3,600 extra burst requests)
shapes = ['Sudden Step\n(10s spike)', 'Linear Ramp\n(60s ramp)', 'Repeated Pulses\n(3x 5s pulses)']
x = np.arange(len(shapes))
width = 0.35

# Empirical Metrics from summary_novelty_metrics.csv
auc_docker = [5.65, 0.00, 1.06]
auc_neon   = [0.27, 0.004, 0.67]

baf_docker = [0.30, -0.03, 0.02]
baf_neon   = [0.21,  0.11, 0.08]

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5.5), dpi=300)

# Subplot 1: Tail Severity (AUC_H)
rects1 = ax1.bar(x - width/2, auc_docker, width, label='Self-Hosted Baseline (Docker Postgres)', 
                 color='#475569', edgecolor='#1e293b', linewidth=1.2, zorder=3)
rects2 = ax1.bar(x + width/2, auc_neon, width, label='Managed Cloud (AWS Neon Serverless)', 
                 color='#2563EB', edgecolor='#1d4ed8', linewidth=1.2, zorder=3)

ax1.set_ylabel(r'Tail Severity Metric $AUC_H$ ($s \cdot ms$)' + '\n(Lower is Better)', fontsize=11, fontweight='bold')
ax1.set_title('Tail Latency Accumulation Above Baseline\n(Iso-Workload = 3,600 extra requests)', fontsize=12, fontweight='bold', pad=12)
ax1.set_xticks(x)
ax1.set_xticklabels(shapes, fontsize=10, fontweight='bold')
ax1.grid(axis='y', linestyle='--', alpha=0.5, zorder=0)
ax1.set_ylim(0, 6.5)

for rect in rects1:
    h = rect.get_height()
    val_str = f"{h:.2f}" if h >= 0.01 else f"{h:.3f}"
    ax1.annotate(val_str, xy=(rect.get_x() + rect.get_width() / 2, h),
                 xytext=(0, 4), textcoords="offset points",
                 ha='center', va='bottom', fontsize=9, fontweight='bold', color='#1e293b')

for rect in rects2:
    h = rect.get_height()
    val_str = f"{h:.2f}" if h >= 0.01 else f"{h:.3f}"
    ax1.annotate(val_str, xy=(rect.get_x() + rect.get_width() / 2, h),
                 xytext=(0, 4), textcoords="offset points",
                 ha='center', va='bottom', fontsize=9, fontweight='bold', color='#1d4ed8')

ax1.annotate('Sudden shock causes 20.8x higher\ntail penalty in Self-Hosted (5.65 vs 0.27)',
             xy=(0, 5.65), xytext=(0.35, 4.8),
             arrowprops=dict(arrowstyle="->", color='#b91c1c', lw=1.5),
             fontsize=9, fontweight='semibold', color='#991b1b',
             bbox=dict(boxstyle="round,pad=0.3", fc="#fee2e2", ec="#f87171", lw=1))

# Subplot 2: Burst Amplification Factor (BAF)
rects3 = ax2.bar(x - width/2, baf_docker, width, label='Self-Hosted Baseline (Docker Postgres)', 
                 color='#475569', edgecolor='#1e293b', linewidth=1.2, zorder=3)
rects4 = ax2.bar(x + width/2, baf_neon, width, label='Managed Cloud (AWS Neon Serverless)', 
                 color='#2563EB', edgecolor='#1d4ed8', linewidth=1.2, zorder=3)

ax2.set_ylabel('Burst Amplification Factor (BAF)\n(Fractional p99 degradation)', fontsize=11, fontweight='bold')
ax2.set_title('Relative Tail Degradation Under Burst\n($BAF = (p99_{burst} - p99_{base}) / p99_{base}$)', fontsize=12, fontweight='bold', pad=12)
ax2.set_xticks(x)
ax2.set_xticklabels(shapes, fontsize=10, fontweight='bold')
ax2.axhline(0, color='black', linewidth=0.8, linestyle='-')
ax2.grid(axis='y', linestyle='--', alpha=0.5, zorder=0)
ax2.set_ylim(-0.08, 0.40)

for rect in rects3:
    h = rect.get_height()
    va = 'bottom' if h >= 0 else 'top'
    offset = 4 if h >= 0 else -12
    ax2.annotate(f"{h:+.2f}", xy=(rect.get_x() + rect.get_width() / 2, h),
                 xytext=(0, offset), textcoords="offset points",
                 ha='center', va=va, fontsize=9, fontweight='bold', color='#1e293b')

for rect in rects4:
    h = rect.get_height()
    va = 'bottom' if h >= 0 else 'top'
    offset = 4 if h >= 0 else -12
    ax2.annotate(f"{h:+.2f}", xy=(rect.get_x() + rect.get_width() / 2, h),
                 xytext=(0, offset), textcoords="offset points",
                 ha='center', va=va, fontsize=9, fontweight='bold', color='#1d4ed8')

handles, labels = ax1.get_legend_handles_labels()
fig.legend(handles, labels, loc='lower center', ncol=2, frameon=True, fontsize=11, 
           bbox_to_anchor=(0.5, -0.05), edgecolor='#cbd5e1')

plt.suptitle('NOVELTY EVALUATION: Iso-Workload Burst Shape Sensitivity Analysis\nSelf-Hosted (Docker Postgres) vs Managed Cloud (AWS Neon) under Step, Ramp, & Pulses', 
             fontsize=13, fontweight='bold', y=1.03)

plt.tight_layout()
plt.savefig(out_file, dpi=300, bbox_inches='tight')
plt.close()

print(f"SUCCESS: Brand-new figure saved at: {out_file}")
