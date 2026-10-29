"""Stage-9 (QIP) analysis: Vrana et al. (NJP 16, 073033, 2014) baselines on the existing E3 data and the E10 hardware data.
(V1) known-p rule of Vrana Sec. II C: k_V = argmin_k (k+1)/(-log(1-P_lam(k))) with lam from the 1p fit on training seeds
     (their objective: queries for a target failure probability), evaluated by our expected cost on test seeds.
(V2) fault-ignorant Algorithm 1 of Vrana Sec. II D (no knowledge of p): rounds g = 0,1,2,... with
     k_g = floor(alpha_g * (pi/4) sqrt(N)), alpha_g = (1 + g/(c log(1/eps)))^(-1/2), c = 10; each round costs k_g + 1 queries
     (k_g iterations + 1 verification). Expected queries until the first verified success, using empirical P(k).
Input: NB1 results folder (e3_counts.csv) and optional hardware folder (hw_counts.csv, hw_summary.csv)."""
import sys, itertools, numpy as np, pandas as pd
sys.path.insert(0, "/home/claude/nb")
from grover_lib import fit_lambda, p_noisy, r_opt

R = sys.argv[1] if len(sys.argv) > 1 else "/home/claude/kaggle/merged"
HW = sys.argv[2] if len(sys.argv) > 2 else "/home/claude/hw/results_hw"
C_CONST = 10.0


def alg1_cost(P, N, eps, c=C_CONST, gmax=2_000_000):
    """Expected queries until first success for Vrana Algorithm 1; P: dict k -> success probability."""
    base = np.pi / 4 * np.sqrt(N); L = c * np.log(1 / eps)
    exp_cost, surv, g = 0.0, 1.0, 0
    while surv > 1e-12 and g < gmax:
        k = int(np.floor(base / np.sqrt(1 + g / L)))
        exp_cost += surv * (k + 1); surv *= 1 - P[k]; g += 1
    return exp_cost, g


def kV(lam, N, kg):
    pl = np.clip(p_noisy(kg, N, lam), 1e-15, 1 - 1e-15)
    return int(kg[np.argmin((kg + 1) / -np.log(1 - pl))])


e3 = pd.read_csv(f"{R}/e3_counts.csv"); seeds = sorted(e3.seed.unique()); rows = []
for (b, n), g in e3.groupby(["backend", "n"]):
    N = 2 ** n; kg = np.arange(0, int(g.k.max()) + 1)
    for tr in itertools.combinations(seeds, 2):
        te = [s for s in seeds if s not in tr]
        a = g[g.seed.isin(tr)].groupby("k")[["succ", "shots"]].sum()
        t = g[g.seed.isin(te)].groupby("k")[["succ", "shots"]].sum()
        ks = t.index.values; Pt = t.succ.values / t.shots.values; c = (ks + 1) / np.maximum(Pt, 1e-12); cmin = c.min()
        f1 = fit_lambda(a.index.values, a.succ.values, a.shots.values, N, "1p")
        k1 = int(kg[np.argmin((kg + 1) / p_noisy(kg, N, f1["lam"]))])
        kv = kV(f1["lam"], N, kg)
        base = dict(backend=b, n=n, split=str(tuple(int(x) for x in tr)), cmin=cmin, classical=(N + 1) / 2)
        rows.append({**base, "rule": "1p (ours)", "k": k1, "cost": c[k1]})
        rows.append({**base, "rule": "Vrana known-p", "k": kv, "cost": c[kv]})
        Pd = dict(zip(ks, Pt))
        for eps in (0.1, 0.01, 0.001):
            ca, _ = alg1_cost(Pd, N, eps)
            rows.append({**base, "rule": f"Vrana Alg.1 eps={eps}", "k": int(np.floor(np.pi / 4 * np.sqrt(N))), "cost": ca})
        rows.append({**base, "rule": "R_opt", "k": r_opt(N), "cost": c[r_opt(N)]})
d = pd.DataFrame(rows); d["regret"] = d.cost / d.cmin - 1; d["vs_classical"] = d.cost / d.classical
d.to_csv(f"{R}/e11_vrana.csv", index=False)
print("Regret over 18 cells x 10 splits:")
s = d.groupby("rule").agg(mean_regret=("regret", "mean"), median=("regret", "median"), max=("regret", "max"),
                          worse_than_classical=("vs_classical", lambda x: int((x > 1).sum())))
print(s.round(4).to_string())
cell = d.groupby(["backend", "n", "rule"]).agg(cost=("cost", "mean"), regret=("regret", "mean"), classical=("classical", "first")).reset_index()
cell.to_csv(f"{R}/e11_vrana_cells.csv", index=False)
print(cell.pivot_table(index=["backend", "n"], columns="rule", values="regret").round(3).to_string())
print("k_V == k_1p share:", (d[d.rule == "Vrana known-p"].k.values == d[d.rule == "1p (ours)"].k.values).mean())

# hardware (single run; fit on all data)
try:
    h = pd.read_csv(f"{HW}/hw_counts.csv"); hs = pd.read_csv(f"{HW}/hw_summary.csv"); hr = []
    for n, g in h.groupby("n"):
        g = g.groupby("k")[["succ", "shots"]].sum().reset_index()  # pool layouts (run 2 has two transpiler seeds)
        N = 2 ** n; ks = g.k.values; P = g.succ.values / g.shots.values; c = (ks + 1) / np.maximum(P, 1e-12); cmin = c.min()
        lam = hs[(hs.source == "hardware") & (hs.n == n)].lam_1p.item(); kg = np.arange(0, ks.max() + 1)
        kv = kV(lam, N, kg); Pd = dict(zip(ks, P))
        r = dict(n=n, cmin=cmin, classical=(N + 1) / 2, k_1p=int(hs[(hs.source == "hardware") & (hs.n == n)].k_1p.item()), k_V=kv,
                 cost_V=c[kv])
        for eps in (0.1, 0.01, 0.001):
            r[f"alg1_eps{eps}"] = alg1_cost(Pd, N, eps)[0]
        hr.append(r)
    hr = pd.DataFrame(hr)
    for col in ["cost_V", "alg1_eps0.1", "alg1_eps0.01", "alg1_eps0.001"]:
        hr["regret_" + col] = hr[col] / hr.cmin - 1
    hr.to_csv(f"{HW}/hw_vrana.csv", index=False); print("\nHardware:"); print(hr.round(3).to_string())
except FileNotFoundError:
    print("no hardware folder")
