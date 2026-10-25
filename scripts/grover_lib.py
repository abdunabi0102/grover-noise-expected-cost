"""Shared code for the Grover-under-noise experiments (E1-E4).
Qiskit >= 2.0, qiskit-aer >= 0.17, qiskit-ibm-runtime >= 0.40 (fake backends)."""
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)  # QuantumCircuit.mcx(mode=...) deprecated in Qiskit 2.1; behaviour unchanged in 2.6.1
import numpy as np
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister, transpile

# ---------- theory (Eqs. 10, 13, 18-20 of the manuscript) ----------
def theta(N, M=1):
    return np.arcsin(np.sqrt(M / N))

def p_ideal(k, N, M=1):
    return np.sin((2 * np.asarray(k) + 1) * theta(N, M)) ** 2

def p_noisy(k, N, lam, M=1):
    q = 1.0 - lam
    k = np.asarray(k, dtype=float)
    return q ** k * p_ideal(k, N, M) + (1 - q ** k) * M / N

def r_opt(N, M=1):
    return int(round(np.pi / (4 * theta(N, M)) - 0.5))

# ---------- circuits ----------
def _mcz(qc, qubits, anc, mode):
    """Multi-controlled Z on `qubits` (last one is the target of the MCX)."""
    *ctrl, tgt = qubits
    qc.h(tgt)
    if len(ctrl) == 1:
        qc.cx(ctrl[0], tgt)
    elif len(ctrl) == 2:
        qc.ccx(ctrl[0], ctrl[1], tgt)
    elif mode == "v-chain" and anc is not None and len(anc) > 0:
        qc.mcx(ctrl, tgt, ancilla_qubits=list(anc), mode="v-chain")
    else:
        qc.mcx(ctrl, tgt)  # synthesised by the transpiler (ancilla-free)
    qc.h(tgt)

def grover_circuit(n, target, k, mode="noancilla", measure=True):
    """n-qubit single-target Grover circuit with k iterations.
    Qubit i carries bit 2**i, so the measured bitstring equals format(target, f'0{n}b')
    and x1 (MSB in the manuscript convention) is qubit n-1."""
    q = QuantumRegister(n, "q")
    regs = [q]
    anc = None
    if mode == "v-chain" and n >= 4:
        anc = QuantumRegister(n - 3, "a")
        regs.append(anc)
    if measure:
        regs.append(ClassicalRegister(n, "c"))
    qc = QuantumCircuit(*regs, name=f"grover_n{n}_k{k}")
    zeros = [i for i in range(n) if not (target >> i) & 1]
    qc.h(q)
    for _ in range(k):
        # oracle O = I - 2|x0><x0|
        if zeros:
            qc.x([q[i] for i in zeros])
        _mcz(qc, list(q), anc, mode)
        if zeros:
            qc.x([q[i] for i in zeros])
        # diffusion D = 2|psi0><psi0| - I  (up to global phase -1)
        qc.h(q); qc.x(q)
        _mcz(qc, list(q), anc, mode)
        qc.x(q); qc.h(q)
    if measure:
        qc.measure(q, regs[-1])
    return qc

# ---------- resource metrics ----------
TWO_Q = ("ecr", "cz", "cx")

def resources(tqc):
    ops = tqc.count_ops()
    n2q = sum(v for g, v in ops.items() if g in TWO_Q)
    active = {tqc.find_bit(qb).index for inst in tqc.data
              if inst.operation.name not in ("barrier", "delay") for qb in inst.qubits}
    d2 = tqc.depth(filter_function=lambda inst: inst.operation.num_qubits == 2)
    return dict(depth=tqc.depth(), depth_2q=d2, n_2q=n2q,
                n_1q=sum(v for g, v in ops.items() if g in ("rz", "sx", "x")),
                n_ops=sum(v for g, v in ops.items() if g not in ("barrier", "measure", "delay")),
                phys_qubits=len(active))

# ---------- statistics ----------
def wilson(s, n, z=1.959964):
    p = s / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return c - h, c + h

def _nll(params, ks, succ, shots, N, model):
    if model == "1p":
        lam, A = params[0], 1.0
    else:
        lam, A = params
    q = 1 - lam
    pk = A * q ** ks * p_ideal(ks, N) + (1 - A * q ** ks) / N
    pk = np.clip(pk, 1e-12, 1 - 1e-12)
    return -np.sum(succ * np.log(pk) + (shots - succ) * np.log(1 - pk))

def fit_lambda(ks, succ, shots, N, model="1p"):
    """Binomial MLE of lambda_eff (model '1p': Eq. 18) or (lambda, A) (model '2p':
    A <= 1 absorbs a k-independent SPAM/initialisation loss)."""
    from scipy.optimize import minimize, minimize_scalar
    ks, succ, shots = map(np.asarray, (ks, succ, shots))
    if model == "1p":
        r = minimize_scalar(lambda l: _nll([l], ks, succ, shots, N, "1p"),
                            bounds=(0.0, 0.999), method="bounded")
        return dict(lam=r.x, A=1.0, nll=r.fun)
    best = None
    for l0 in (0.05, 0.3, 0.7):
        r = minimize(lambda p: _nll(p, ks, succ, shots, N, "2p"), x0=[l0, 0.9],
                     bounds=[(0.0, 0.999), (0.0, 1.0)], method="L-BFGS-B")
        if best is None or r.fun < best.fun:
            best = r
    return dict(lam=best.x[0], A=best.x[1], nll=best.fun)

def expected_cost(ks, phat):
    phat = np.maximum(np.asarray(phat, float), 1e-12)
    return (np.asarray(ks) + 1) / phat

def speedup_from_cost(N, cost):
    return (N + 1) / 2 / np.min(cost)
