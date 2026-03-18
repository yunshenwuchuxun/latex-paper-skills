# Method Positioning (Bullets Only)

Core idea
- We model real-time reservoir operation as a periodic decision cycle that links: (i) observation/state snapshot, (ii) rolling parameter calibration for inflow forecasting, (iii) uncertainty-aware dispatch optimization, and (iv) implementation feedback that updates the next cycle.

Closest prior work clusters (representative)
- Online/rolling calibration and data assimilation in hydrology: EnKF dual estimation and time-varying parameters (e.g., `moradkhani2005dual`, `xiong2019identifying`, `maxwell2018constraining`, `evensen2003ensemble`).
- Inflow/streamflow forecasting and multi-step ML baselines: complementary modeling and neural hydrology at scale (e.g., `gragne2015improving`, `kratzert2018rainfall`, `kratzert2019learning`, `fan2023explainable`).
- Forecast value and forecast-informed operations: forecast skill does not translate monotonically to operational value (e.g., `turner2017complex`).
- Uncertainty-aware dispatch and MPC for reservoirs: scenario-based MPC and uncertainty-period-aware rules (e.g., `cestari2023scenario`, `liu2020reservoir`, `mayne2000constrained`).
- Forecast-informed reservoir operation with ML (FIRO-style settings): operational policies learned from forecasts (e.g., `zarei2021machine`).

What the proposed paper contributes (claim alignment)
- C1: A closed-loop coupling that explicitly feeds realized implementation outcomes back into the next cycle, rather than treating dispatch as an open-loop plan.
- C2: Rolling calibration framed as a guardrail against nonstationarity; evaluated both by forecast metrics (RMSE/NSE/CRPS) and by operational metrics.
- C3: Uncertainty-aware dispatch (scenario/ensemble MPC) integrated into the same loop; ablated against deterministic variants.
- C4: A deployment-facing specification: data cadence, runtime per cycle, and failure modes (sparse/delayed observations).

What we do NOT claim (non-goals)
- We do not claim a new deep-learning architecture for inflow forecasting.
- We do not claim universal superiority across all basins/reservoir objectives; generality is tested only when data permit.
- We do not claim climate attribution or long-horizon seasonal planning impacts.

Likely reviewer objections and planned responses
- Objection: "This is a combination of known components."
  - Response: make the coupling explicit, quantify marginal value of each coupling edge via ablations (no rolling calibration / no uncertainty propagation / no feedback).
- Objection: "Improvements could be due to better forecasts, not coupling."
  - Response: separate forecast-only gains (C2) from operations-only gains (C1/C3) using matched forecast inputs and dispatch ablations.
- Objection: "Site-specific case study."
  - Response: include regime-shift stress tests and, if available, a second reservoir; otherwise state limits explicitly.
