"""Stage-8 analysis: regret-based evaluation of k-selection rules over all C(5,2)=10 train/test seed splits,
naive baselines, per-seed lambda fits, and GOF of the 2p model. Input: NB1 results folder."""
import sys, os, itertools, numpy as np, pandas as pd
from scipy.stats import chi2
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from grover_lib import fit_lambda, p_ideal, p_noisy, r_opt
R = sys.argv[1] if len(sys.argv) > 1 else "../results"
e3 = pd.read_csv(f"{R}/e3_counts.csv"); e4 = pd.read_csv(f"{R}/e4_summary.csv")
seeds = sorted(e3.seed.unique()); rows = []
for (b, n), g in e3.groupby(["backend", "n"]):
    N = 2 ** n; kg = np.arange(0, 4 * int(np.sqrt(N)) + 21)
    lam_cal = e4[(e4.backend == b) & (e4.n == n)].lam_cal.item()
    k_cal = int(kg[np.argmin((kg + 1) / p_noisy(kg, N, lam_cal))])
    for tr in itertools.combinations(seeds, 2):
        te = [s for s in seeds if s not in tr]
        a = g[g.seed.isin(tr)].groupby("k")[["succ", "shots"]].sum()
        t = g[g.seed.isin(te)].groupby("k")[["succ", "shots"]].sum()
        ks = t.index.values; c = (ks + 1) / np.maximum(t.succ.values / t.shots.values, 1e-12); cmin = c.min()
        f1 = fit_lambda(a.index.values, a.succ.values, a.shots.values, N, "1p")
        f2 = fit_lambda(a.index.values, a.succ.values, a.shots.values, N, "2p"); q = 1 - f2["lam"]
        k1 = int(kg[np.argmin((kg + 1) / p_noisy(kg, N, f1["lam"]))])
        k2 = int(kg[np.argmin((kg + 1) / (f2["A"] * q ** kg * p_ideal(kg, N) + (1 - f2["A"] * q ** kg) / N))])
        ca = (a.index.values + 1) / np.maximum(a.succ.values / a.shots.values, 1e-12); k_emp = int(a.index.values[np.argmin(ca)])
        rules = {"1p": k1, "2p": k2, "cal": k_cal, "emp_train": k_emp, "k=1": 1, "R_opt": r_opt(N)}
        for r, k in rules.items():
            rows.append(dict(backend=b, n=n, split=str(tr), rule=r, k=k, k_best_test=int(ks[np.argmin(c)]), regret=c[k] / cmin - 1))
reg = pd.DataFrame(rows); reg.to_csv(f"{R}/e4d_regret_splits.csv", index=False)
summ = reg.groupby("rule").regret.agg(mean="mean", median="median", p90=lambda x: x.quantile(0.9), max="max")
summ["exact_match_rate"] = reg.assign(m=reg.k == reg.k_best_test).groupby("rule").m.mean()
print("Regret over 18 cells x 10 splits (=180 evaluations):"); print(summ.round(4).to_string())
# per-seed 1p fits
ps = []
for (b, n, s), g in e3.groupby(["backend", "n", "seed"]):
    f = fit_lambda(g.k.values, g.succ.values, g.shots.values, 2 ** n, "1p")
    ph = np.clip(g.succ.values / g.shots.values, 1e-12, 1 - 1e-12)
    sat = -np.sum(g.succ.values * np.log(ph) + (g.shots.values - g.succ.values) * np.log(1 - ph))
    dev = 2 * (f["nll"] - sat); ps.append(dict(backend=b, n=n, seed=s, lam=f["lam"], dev=dev, df=len(g) - 1, p=chi2.sf(dev, len(g) - 1)))
ps = pd.DataFrame(ps); ps.to_csv(f"{R}/e3b_perseed_fits.csv", index=False)
agg = ps.groupby(["backend", "n"]).agg(lam_min=("lam", "min"), lam_max=("lam", "max"), n_reject=("p", lambda x: (x < 0.05 / 90).sum()))
print("\nPer-seed 1p fits (90 fits; rejections at Bonferroni 0.05/90):"); print(agg.round(3).to_string()); print("total per-seed rejections:", int(agg.n_reject.sum()), "of 90")
# GOF of 2p (pooled)
g2 = []
for (b, n), g in e3.groupby(["backend", "n"]):
    a = g.groupby("k")[["succ", "shots"]].sum(); f2 = fit_lambda(a.index.values, a.succ.values, a.shots.values, 2 ** n, "2p")
    ph = np.clip(a.succ.values / a.shots.values, 1e-12, 1 - 1e-12)
    sat = -np.sum(a.succ.values * np.log(ph) + (a.shots.values - a.succ.values) * np.log(1 - ph))
    dev = 2 * (f2["nll"] - sat); g2.append(dict(backend=b, n=n, dev2=dev, df=len(a) - 2, p=chi2.sf(dev, len(a) - 2)))
g2 = pd.DataFrame(g2); g2.to_csv(f"{R}/e3c_gof_2p.csv", index=False)
print("\n2p pooled GOF: rejected (p<0.05/18):", int((g2.p < 0.05 / 18).sum()), "of 18; max p =", g2.p.max())
