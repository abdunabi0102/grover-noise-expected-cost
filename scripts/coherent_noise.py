"""E9: coherent (systematic over-rotation) errors, which are absent from fake-backend noise models.
After every CZ a ZZ-rotation exp(-i eps/2 Z⊗Z) and after every sx an extra RX(eps) are applied (same angle every time).
All-to-all CZ basis, n = 3-5, eps in {0.02, 0.05, 0.1, 0.2} rad; 3 seeds x 8192 shots."""
import sys, os, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from grover_lib import *
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, coherent_unitary_error
from qiskit.circuit.library import RZZGate, RXGate
from qiskit.quantum_info import Operator
from scipy.stats import chi2
OUT = sys.argv[1] if len(sys.argv) > 1 else "../results"
BASIS = ["rz", "sx", "x", "cz"]
def nm(eps):
    m = NoiseModel(basis_gates=BASIS)
    m.add_all_qubit_quantum_error(coherent_unitary_error(Operator(RZZGate(eps))), ["cz"])
    m.add_all_qubit_quantum_error(coherent_unitary_error(Operator(RXGate(eps))), ["sx"])
    return m
rows = []
for n in [3, 4, 5]:
    N = 2 ** n; t = 107 % N; key = format(t, f"0{n}b"); K = 2 * r_opt(N) + 2
    circs = [transpile(grover_circuit(n, t, k, "v-chain"), basis_gates=BASIS, optimization_level=3, seed_transpiler=0) for k in range(K + 1)]
    for eps in [0.02, 0.05, 0.1, 0.2]:
        sim = AerSimulator(noise_model=nm(eps)); succ = np.zeros(K + 1); shots = np.zeros(K + 1)
        for s in [0, 1, 2]:
            res = sim.run(circs, shots=8192, seed_simulator=3000 + s).result()
            for k in range(K + 1): succ[k] += res.get_counts(k).get(key, 0); shots[k] += 8192
        ks = np.arange(K + 1); f1 = fit_lambda(ks, succ, shots, N, "1p")
        ph = np.clip(succ / shots, 1e-12, 1 - 1e-12)
        sat = -np.sum(succ * np.log(ph) + (shots - succ) * np.log(1 - ph)); dev = 2 * (f1["nll"] - sat)
        c = (ks + 1) / ph; kg = np.arange(0, 4 * int(np.sqrt(N)) + 21)
        k1 = int(kg[np.argmin((kg + 1) / p_noisy(kg, N, f1["lam"]))])
        rows.append(dict(n=n, eps=eps, lam_1p=f1["lam"], p_gof=chi2.sf(dev, K), k_emp=int(ks[np.argmin(c)]), k_1p=k1,
                         regret_1p=c[min(k1, K)] / c.min() - 1, S_emp=(N + 1) / 2 / c.min(), S_1p=(N + 1) / 2 / ((kg + 1) / p_noisy(kg, N, f1["lam"])).min(),
                         P_emp_max=ph.max(), k_Pmax=int(ks[np.argmax(ph)]), R_opt=r_opt(N)))
df = pd.DataFrame(rows); df.to_csv(f"{OUT}/e9_coherent.csv", index=False); print(df.round(4).to_string())
