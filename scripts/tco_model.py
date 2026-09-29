import os
import pandas as pd
import matplotlib.pyplot as plt

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

def calculate_3yr_tco(dba_hourly_rate=50.0, monthly_infra_managed=150.0, monthly_infra_selfhosted=45.0,
                     dba_hours_managed_per_month=3.0, dba_hours_selfhosted_per_month=25.0):
    """
    Calculates 3-Year Total Cost of Ownership (TCO) comparing Managed vs. Self-Hosted DB deployments.
    TCO = (Monthly Infrastructure Charge * 36) + (DBA Hours/Month * 36 * Hourly Labor Rate)
    """
    months = 36
    
    infra_managed_total = monthly_infra_managed * months
    dba_managed_total = dba_hours_managed_per_month * months * dba_hourly_rate
    tco_managed = infra_managed_total + dba_managed_total
    
    infra_selfhosted_total = monthly_infra_selfhosted * months
    dba_selfhosted_total = dba_hours_selfhosted_per_month * months * dba_hourly_rate
    tco_selfhosted = infra_selfhosted_total + dba_selfhosted_total
    
    return {
        "dba_hourly_rate": dba_hourly_rate,
        "tco_managed": tco_managed,
        "infra_managed": infra_managed_total,
        "dba_managed": dba_managed_total,
        "tco_selfhosted": tco_selfhosted,
        "infra_selfhosted": infra_selfhosted_total,
        "dba_selfhosted": dba_selfhosted_total,
        "cost_difference": tco_managed - tco_selfhosted
    }

def run_tco_sensitivity_sweep():
    """Sweeps DBA hourly rates from $0/hr to $120/hr to identify crossover conditions."""
    hourly_rates = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 120]
    results = []
    
    for rate in hourly_rates:
        res = calculate_3yr_tco(dba_hourly_rate=rate)
        results.append(res)
        
    df = pd.DataFrame(results)
    
    print("=== 3-YEAR TOTAL COST OF OWNERSHIP (TCO) SENSITIVITY TABLE ===")
    print(df[["dba_hourly_rate", "infra_managed", "dba_managed", "tco_managed", 
              "infra_selfhosted", "dba_selfhosted", "tco_selfhosted"]].to_string(index=False))
    
    # Save CSV
    csv_path = os.path.join(LOG_DIR, "tco_sensitivity_analysis.csv")
    df.to_csv(csv_path, index=False)
    print(f"\nSaved TCO sensitivity data to {csv_path}")
    
    # Generate Crossover Chart
    plt.figure(figsize=(9, 5))
    plt.plot(df["dba_hourly_rate"], df["tco_managed"], label="Managed DB (e.g. Cloud SQL / RDS)", color="blue", linewidth=2.5, marker="o")
    plt.plot(df["dba_hourly_rate"], df["tco_selfhosted"], label="Self-Hosted DB (Docker VM)", color="red", linewidth=2.5, marker="s")
    
    plt.title("3-Year Total Cost of Ownership (TCO) vs DBA Hourly Labor Cost", fontsize=12, fontweight="bold")
    plt.xlabel("DBA Administrative Labor Rate ($ / hour)", fontsize=10)
    plt.ylabel("3-Year Total Cost ($ USD)", fontsize=10)
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.legend(fontsize=10)
    plt.tight_layout()
    
    chart_path = os.path.join(LOG_DIR, "tco_crossover_chart.png")
    plt.savefig(chart_path, dpi=300)
    print(f"Saved TCO Crossover Chart to {chart_path}")

if __name__ == "__main__":
    run_tco_sensitivity_sweep()
