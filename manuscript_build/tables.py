import pandas as pd, numpy as np
R="/home/claude/kaggle/merged/"
B=["FakeSherbrooke","FakeTorino","FakeFez"]
S_={"FakeSherbrooke":"Sherbrooke","FakeTorino":"Torino","FakeFez":"Fez"}
def f(x,d=3): return f"{x:.{d}f}"
out={}
# Table 7: resources n=7 k=8 both modes, opt3
e2=pd.read_csv(R+"e2_resources.csv"); e2=e2[e2.opt==3]
g=e2.groupby(["backend","mode","n","k"]).mean(numeric_only=True).reset_index()
rows=["| Device model | MCX synthesis | Qubits (circuit) | Physical qubits | Depth | Two-qubit depth | Two-qubit gates | Single-qubit gates |","|---|---|---|---|---|---|---|---|"]
for b in B:
    for m,lab in [("noancilla","ancilla-free"),("v-chain","ancilla-assisted")]:
        r=g[(g.backend==b)&(g["mode"]==m)&(g.n==7)&(g.k==8)].iloc[0]
        rows.append(f"| {S_[b]} | {lab} | {int(r.logical_qubits)} | {r.phys_qubits:.1f} | {r.depth:,.0f} | {r.depth_2q:,.0f} | {r.n_2q:,.0f} | {r.n_1q:,.0f} |")
out["T7"]="\n".join(rows)
# Table 7b: per n v-chain k=R_opt per backend 2q gates
rows=["| n | R~opt~ | Qubits (circuit) | "+" | ".join(f"{S_[b]}: depth / 2q gates" for b in B)+" |","|---|---|---|---|---|---|"]
from math import asin,pi,sqrt
for n in range(2,8):
    N=2**n; R_=round(pi/(4*asin(N**-0.5))-0.5)
    cells=[]
    for b in B:
        r=g[(g.backend==b)&(g["mode"]=="v-chain")&(g.n==n)&(g.k==R_)].iloc[0]
        cells.append(f"{r.depth:,.0f} / {r.n_2q:,.0f}")
    q=int(g[(g["mode"]=="v-chain")&(g.n==n)].logical_qubits.iloc[0])
    rows.append(f"| {n} | {R_} | {q} | "+" | ".join(cells)+" |")
out["T7b"]="\n".join(rows)
# Table 8: lambda fits
fits=pd.read_csv(R+"e3_fits.csv")
rows=["| n | "+" | ".join(f"{S_[b]}: λ~eff~ [95% CI]" for b in B)+" | "+" | ".join(f"{S_[b]}: A (λ~2p~)" for b in B)+" |","|"+"---|"*7]
for n in range(2,8):
    c=[];a=[]
    for b in B:
        r=fits[(fits.backend==b)&(fits.n==n)].iloc[0]
        c.append(f"{r.lam_1p:.3f} [{r.lam_lo:.3f}, {r.lam_hi:.3f}]"); a.append(f"{r.A_2p:.2f} ({r.lam_2p:.3f})")
    rows.append(f"| {n} | "+" | ".join(c)+" | "+" | ".join(a)+" |")
out["T8"]="\n".join(rows)
# Table 9: predictions
p=pd.read_csv(R+"e4b_model_predictions.csv"); s=pd.read_csv(R+"e4_summary.csv")
rows=["| Device model | n | k̂\\*~C~ | k\\*~C~ (1p) | k\\*~C~ (2p) | k\\*~C~ (cal.) | Ŝ [95% CI] | S (1p) | S (2p) |","|---|---|---|---|---|---|---|---|---|"]
for b in B:
    for n in range(2,8):
        r=p[(p.backend==b)&(p.n==n)].iloc[0]
        rows.append(f"| {S_[b]} | {n} | {r.kC_emp} | {r.kC_pred_1p} | {r.kC_pred_2p} | {r.kC_pred_cal} | {r.S_hat:.2f} [{r.S_lo:.2f}, {r.S_hi:.2f}] | {r.S_pred_1p:.2f} | {r.S_pred_2p:.2f} |")
out["T9"]="\n".join(rows)
# Table 10: baselines n=5,6,7
e6=pd.read_csv(R+"e6_baselines.csv")
rows=["| Device model | n | Classical | Grover, k = R~opt~ | BBHT | Cost-optimal k (held out) |","|---|---|---|---|---|---|"]
for b in B:
    for n in [5,6,7]:
        d=e6[(e6.backend==b)&(e6.n==n)].set_index("strategy")
        def c(sname,k=False):
            r=d.loc[sname]; s=f"{r.exp_queries:.1f} [{r.lo:.1f}, {r.hi:.1f}]"
            if k: s+=f" (k = {int(r.k_used)})"
            return s
        rows.append(f"| {S_[b]} | {n} | {d.loc['classical'].exp_queries:.1f} | {c('grover_Ropt',True)} | {c('BBHT')} | {c('ours_heldout',True)} |")
out["T10"]="\n".join(rows)
# Table 11: local noise subset
e5=pd.read_csv(R+"e5_local_noise.csv")
rows=["| Channel | n | m₂q | p = 0.001 | p = 0.002 | p = 0.005 | p = 0.01 | p = 0.02 | p = 0.05 |","|---|---|---|---|---|---|---|---|---|"]
for ch,lab in [("local_depolarizing","depolarizing"),("amp+phase_damping","amplitude + phase damping")]:
    for n in [3,4,5]:
        d=e5[(e5.channel==ch)&(e5.n==n)].sort_values("p")
        rows.append(f"| {lab} | {n} | {d.n2q_per_iter.iloc[0]:.1f} | "+" | ".join(f"{x:.2f}" for x in d.ratio_lam_over_n2q_p)+" |")
out["T11"]="\n".join(rows)
# misc numbers
out["count"]=dict(k1p=int((p.kC_pred_1p==p.kC_emp).sum()),k2p=int((p.kC_pred_2p==p.kC_emp).sum()),kcal=int((p.kC_pred_cal==p.kC_emp).sum()),ci1=int(p.in_CI_1p.sum()),ci2=int(p.in_CI_2p.sum()),
 lrt=int((fits.p_LRT<0.05).sum()), gof=int((fits.p_gof_1p<1e-4).sum()), Smin=s.S_hat.min(), Smax=s.S_hat.max(), lamcal_lower=int((s.lam_cal<s.lam_fit).sum()),
 heldout_vs_best=((e6[e6.strategy=='ours_heldout'].set_index(['backend','n']).exp_queries/e6[e6.strategy=='best_k_insample'].set_index(['backend','n']).exp_queries)-1).max())
import json; json.dump(out,open("tables.json","w"),indent=1,default=float)
for k,v in out.items(): print(k); print(v); print()

# ---- Stage-8 additions ----
reg=pd.read_csv(R+"e4d_regret_splits.csv")
lab={"1p":"Model 1p, fitted on training seeds","2p":"Model 2p, fitted on training seeds","cal":"Calibration only, Eq. (31) (no Grover data)","emp_train":"Empirical best $k$ on training seeds","k=1":"Always $k=1$","R_opt":"Always $k=R_{\\mathrm{opt}}$"}
rows=["| Selection rule | Mean excess cost | Median | 90th percentile | Maximum | Exact optimum |","|---|---|---|---|---|---|"]
for r in ["1p","emp_train","cal","2p","k=1","R_opt"]:
    x=reg[reg.rule==r]; m=(x.k==x.k_best_test).mean()
    rows.append(f"| {lab[r]} | {100*x.regret.mean():.1f}% | {100*x.regret.median():.1f}% | {100*x.regret.quantile(0.9):.1f}% | {100*x.regret.max():.0f}% | {100*m:.0f}% |")
out["TA2"]="\n".join(rows)
co=pd.read_csv(R+"e9_coherent.csv")
rows=["| n | ε (rad) | λ~eff~ | k̂\\*~C~ | k\\*~C~ (1p) | Ŝ | S (1p) |","|---|---|---|---|---|---|---|"]
for _,r in co.iterrows():
    rows.append(f"| {int(r.n)} | {r.eps:.2f} | {r.lam_1p:.3f} | {int(r.k_emp)} | {int(r.k_1p)} | {r.S_emp:.2f} | {r.S_1p:.2f} |")
out["TA3"]="\n".join(rows)
json.dump(out,open("tables.json","w"),indent=1,default=float)

# ---- Stage-9 (QIP) additions: hardware runs (E10) and Vrana baselines (E11) ----
from math import asin
RUNS=[("ibm_fez","/home/claude/hw/results_hw/"),("ibm_marrakesh","/home/claude/hw/results_hw_run2/")]
rows=["| Processor | n | Depth / 2q gates at k=R~opt~ | λ~cal~ | λ~eff~ (1p) | A (2p) | k̂\\*~C~ | k\\*~C~ (1p) | Ŝ (95% CI) | S (1p) | Ŝ (sim.) | Regret: k=1 | Regret: R~opt~ |","|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
for dev,HW in RUNS:
    hs=pd.read_csv(HW+"hw_summary.csv"); hr=pd.read_csv(HW+"hw_rules.csv"); res=pd.read_csv(HW+"hw_resources.csv")
    for n in [2,3,4,5]:
        N=2**n; Ro=round(pi/(4*asin(N**-0.5))-0.5)
        h=hs[(hs.source=="hardware")&(hs.n==n)].iloc[0]; s=hs[(hs.source=="simulation")&(hs.n==n)].iloc[0]
        rr=res[(res.n==n)&(res.k==Ro)]
        d0,d1,q0,q1=int(rr.depth.min()),int(rr.depth.max()),int(rr.n_2q.min()),int(rr.n_2q.max())
        dq=f"{d0} / {q0}" if (d0==d1 and q0==q1) else f"{d0}–{d1} / {q0}–{q1}"
        g=lambda rule: hr[(hr.n==n)&(hr.rule==rule)].regret.item()
        rows.append(f"| {dev} | {n} | {dq} | {h.lam_cal:.3f} | {h.lam_1p:.3f} | {h.A_2p:.2f} | {int(h.k_emp)} | {int(h.k_1p)} | {h.S_hat:.2f} [{h.S_lo:.2f}, {h.S_hi:.2f}] | {h.S_1p:.2f} | {s.S_hat:.2f} | {100*g('k=1'):.0f}% | {100*g('R_opt'):.0f}% |")
out["T12"]="\n".join(rows)
v=pd.read_csv(R+"e11_vrana.csv")
lab={"1p (ours)":"Model 1p, cost-optimal $k$ (this work)","Vrana known-p":"Vrana et al., known-$p$ round length (their Sec. II C)",
     "Vrana Alg.1 eps=0.1":"Vrana et al., fault-ignorant Algorithm 1, $\\varepsilon=0.1$","Vrana Alg.1 eps=0.01":"Vrana et al., fault-ignorant Algorithm 1, $\\varepsilon=0.01$",
     "Vrana Alg.1 eps=0.001":"Vrana et al., fault-ignorant Algorithm 1, $\\varepsilon=0.001$","R_opt":"Always $k=R_{\\mathrm{opt}}$"}
rows=["| Strategy | Mean excess cost | Median | Maximum | Evaluations worse than classical (of 180) |","|---|---|---|---|---|"]
for r in lab:
    x=v[v.rule==r]
    rows.append(f"| {lab[r]} | {100*x.regret.mean():.1f}% | {100*x.regret.median():.1f}% | {100*x.regret.max():.0f}% | {int((x.vs_classical>1).sum())} |")
out["TA4"]="\n".join(rows)
json.dump(out,open("tables.json","w"),indent=1,default=float)
print(out["T12"]); print(out["TA4"])
