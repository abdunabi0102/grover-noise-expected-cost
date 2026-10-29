"""Figure 9: hardware vs simulation success probability for both hardware runs."""
import sys, numpy as np, pandas as pd, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
sys.path.insert(0, "/home/claude/nb")
from grover_lib import p_ideal, p_noisy, r_opt, wilson
RUNS = [("ibm_fez", sys.argv[1] if len(sys.argv) > 1 else "/home/claude/hw/results_hw"),
        ("ibm_marrakesh", sys.argv[2] if len(sys.argv) > 2 else "/home/claude/hw/results_hw_run2")]
out = sys.argv[3] if len(sys.argv) > 3 else "/home/claude/hw/fig_hw_both.png"
fig, axes = plt.subplots(2, 4, figsize=(13, 5.6))
for row, (dev, d) in enumerate(RUNS):
    hw = pd.read_csv(f"{d}/hw_counts.csv"); sim = pd.read_csv(f"{d}/hw_sim_counts.csv"); summ = pd.read_csv(f"{d}/hw_summary.csv")
    for ax, n in zip(axes[row], [2, 3, 4, 5]):
        N = 2 ** n
        for lab, df, m in [("hardware", hw[hw.n == n], "o"), ("simulation (device noise model)", sim[sim.n == n], "s")]:
            a = df.groupby("k")[["succ", "shots"]].sum().reset_index(); p = a.succ / a.shots; lo, hi = wilson(a.succ.values, a.shots.values)
            ax.errorbar(a.k, p, yerr=[p - lo, hi - p], fmt=m, ms=3.5, capsize=1, label=lab)
        kk = np.arange(0, 2 * r_opt(N) + 3); lam = summ[(summ.source == "hardware") & (summ.n == n)].lam_1p.item()
        ax.plot(kk, p_ideal(kk, N), "k--", lw=1, label="ideal, Eq. (10)"); ax.plot(kk, p_noisy(kk, N, lam), "-", lw=1.2, label="Eq. (18), hardware fit")
        ax.axhline(1 / N, color="grey", ls=":", lw=0.7); ax.set_title(f"{dev}, n = {n}", fontsize=9); ax.set_ylim(-0.02, 1.05)
        if row == 1: ax.set_xlabel("k")
    axes[row][0].set_ylabel("P(success)")
axes[0][0].legend(fontsize=6.5, loc="upper right"); fig.tight_layout(); fig.savefig(out, dpi=250); print(out)
