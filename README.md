# Expected query cost of Grover search under noise — code and data

Code and data for the article *"Expected Query Cost of Grover Search under Per-Iteration Depolarizing Noise: Explicit Speedup Bounds and Circuit-Level Validation on Noisy Device Models"* (A. Mukhamadiyev, Sh. Toirov, N. Saydirasulov, D. Turimov, S. Abdurakhimov; submitted to *Mathematics*, MDPI).

## Contents
| Path | What it is | Paper |
|---|---|---|
| `scripts/verify_numbers.py` | Closed-form values, bounds and limits (Tables 1–6) and the 128-dimensional statevector cross-check | Sections 4–5 |
| `notebooks/NB1_grover_noise_E1-E4.ipynb` | Grover circuits (n = 2–7), compiled resources, noisy simulation on FakeSherbrooke / FakeTorino / FakeFez, λ_eff fits, expected cost and speedup | Sections 6.1–6.4, Tables 7–10, Fig. 6 |
| `notebooks/NB2_local_noise_baselines_E5-E8.ipynb` | Two-parameter predictions, held-out model check (`e4c_heldout.csv`), controlled local noise, baselines (classical, Grover at R_opt, BBHT), misspecified λ, all figures | Sections 6.4–6.7, Tables 10–12, Figs. 1–8, Appendix A |
| `scripts/grover_lib.py` | Shared functions (also embedded in the notebooks) | — |
| `results/` | Output CSV files, figures and `environment.json` of the Kaggle run reported in the paper (Python 3.13.15, NumPy 2.1.3, SciPy 1.16.3) | all |
| `manuscript_build/` | Scripts that turn the CSV files into the manuscript tables | — |

## Reproduce
- **Kaggle or any CPU machine, Python ≥ 3.11:** `pip install -r requirements.txt`
- Run `NB1`, then `NB2`. In NB2, set `NB1_OUT` to the folder holding NB1's `results/`.
- NB1 takes about 1–1.5 h on 2–4 CPU cores; set `QUICK = True` for a 5-minute smoke test.
- Seeds are fixed: transpiler seed s = 0–4, simulator seed 1000 + s; 8192 shots per circuit.
- Fake-backend noise models are the calibration snapshots shipped with `qiskit-ibm-runtime==0.51.0`. Other versions may give slightly different numbers.
- Measurement counts, resource counts and fitted rates are bit-identical across NumPy 2.1.3 and 2.5.3; bootstrap interval end-points can differ in the second or third decimal with other NumPy versions.

## License
Code: MIT License (see `LICENSE`). Data and figures in `results/`: CC BY 4.0.

## Citation
See `CITATION.cff`. Please cite the article once published.
