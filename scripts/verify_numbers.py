"""Independent recomputation of every number in Mathematics_manuscript_2 (Tables 1-7, bounds, thresholds)."""
import numpy as np
from scipy.optimize import brentq

def theta(N): return np.arcsin(N**-0.5)
def P(k, N): return np.sin((2*k+1)*theta(N))**2
def Pl(k, N, lam):
    q = 1-lam
    return q**k*P(k, N) + (1-q**k)/N
def C(k, N, lam): return (k+1)/Pl(k, N, lam)
def S(N, lam):
    kmax = int(4*np.sqrt(N)+20)
    ks = np.arange(0, kmax+1)
    c = C(ks, N, lam)
    i = np.argmin(c)
    return (N+1)/2/c[i], ks[i], c[i]
def UB(N, lam):
    mu = -np.log(1-lam)
    t2 = np.inf if lam == 0 else np.pi**2*np.exp(mu-1)/mu + 1
    return (N+1)/(2*N)*min(np.pi*np.sqrt(N)+1, t2)
def LB(N, lam):
    mu = -np.log(1-lam)
    return 2*(N**2-1)/(N*(np.pi*np.sqrt(N)+4))*np.exp(-np.pi*mu*np.sqrt(N)/4)
def Sinf(lam):
    q = 1-lam; ks = np.arange(0, 5000)
    g = 2*ks*q**ks + 1/(2*(ks+1)); i = np.argmax(g)
    return g[i], ks[i]
def kstar_exact(N, lam):
    th = theta(N); mu = -np.log(1-lam)
    f = lambda phi: 2*th*np.sin(2*phi) - mu*(np.sin(phi)**2 - 1/N)
    phi = brentq(f, th*1.0001, np.pi/2) if lam > 0 else np.pi/2
    return phi/(2*th) - 0.5
def kstar_approx(N, lam):
    th = theta(N); mu = -np.log(1-lam)
    return 0.5*(np.arctan(4*th/mu)/th - 1) if lam > 0 else np.pi/(4*th)-0.5

N = 128
print("theta", theta(N), "pi/(4th)-1/2", np.pi/(4*theta(N))-0.5)

# Statevector cross-check
s = np.full(N, N**-0.5)
print("\nTable 1 (k, a, b, P, Prest) + max |closed - sv|")
for k in range(11):
    if k > 0:
        s[107] *= -1; s = 2*s.mean() - s
    a = np.sin((2*k+1)*theta(N)); b = np.cos((2*k+1)*theta(N))/np.sqrt(N-1)
    err = max(abs(s[107]-a), abs(np.delete(s, 107)-b).max())
    print(k, f"{a:.6f} {b:.6f} {a*a:.6f} {1-a*a:.6f}  err={err:.1e}")

print("\nTable 2/3 at lam=0.03")
for k in range(11):
    print(k, f"P={P(k,N):.4f} C0={C(k,N,0):.3f} Pl={Pl(k,N,.03):.4f} Cl={C(k,N,.03):.3f}")

print("\nTable 4")
for lam in [0, .005, .01, .02, .03, .05, .10, .20, .30, .50, .70]:
    ks = np.arange(0, 12); pk = Pl(ks, N, lam); kP = ks[np.argmax(pk)]
    s_, kc, c = S(N, lam)
    print(lam, kP, f"{pk.max():.4f}", f"{kstar_exact(N,lam):.3f}", f"{kstar_approx(N,lam):.3f}", kc, f"{c:.2f}", f"{s_:.2f}")

# crossovers
print("\nPl(7)=Pl(8) at lam=", brentq(lambda l: Pl(7,N,l)-Pl(8,N,l), 0.01, 0.2))
print("C(5)=C(6) at lam=", brentq(lambda l: C(5,N,l)-C(6,N,l), 0.001, 0.2))
print("Bounds at 0.03, N=128: LB", LB(N,.03), "UB", UB(N,.03), "S", S(N,.03)[0])

print("\nTable 5")
for n in range(3, 8):
    Nn = 2**n; R = round(np.pi/(4*theta(Nn))-0.5)
    print(Nn, f"{Nn**-0.5:.6f} {theta(Nn):.6f}", R, f"{P(R,Nn):.4f}")

print("\nTable 6")
for Nn in [8,16,32,64,128,256,1024,4096,16384,65536,2**20]:
    s0, k0, _ = S(Nn, 0); s3, k3, _ = S(Nn, .03)
    ls = 1/(np.pi*np.sqrt(Nn)); sl = S(Nn, ls)[0]
    lc = brentq(lambda l: S(Nn, l)[0]-1, 0.3, 0.9)
    print(Nn, k0, f"{s0:.2f}", k3, f"{s3:.2f}", f"{ls:.5f}", f"{sl:.2f}", f"{LB(Nn,ls):.2f}", f"{UB(Nn,ls):.2f}", f"{lc:.3f}")

print("\nS_inf(0.03)", Sinf(.03), " S_inf(5/8)", Sinf(5/8), " 2/(e*mu) at .03", 2/(np.e*-np.log(.97)))
for lam in [.01, .03]:
    mu = -np.log(1-lam)
    print("lam", lam, "S_inf", Sinf(lam)[0], "0.736/lam", .736/lam, "Cor1 fixed-lam UB", np.pi**2*np.exp(mu-1)/mu+1)
