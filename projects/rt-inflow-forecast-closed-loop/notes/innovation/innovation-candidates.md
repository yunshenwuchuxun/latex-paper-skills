# Innovation Candidates

Candidate 1: Closed-loop rolling calibration + dispatch coupling
Claim (1 sentence)
- A closed-loop framework that rolls inflow-model parameters and dispatch decisions at each cycle improves operational performance versus open-loop or static-calibration baselines.
Why it matters
- Forecast errors propagate into dispatch; closing the loop reduces risk under nonstationary conditions.
What existing work covers
- Forecast-informed operation and MPC for reservoirs; ensemble/uncertainty-aware dispatch; real-time inflow forecasting.
Gap
- Limited integration of rolling parameter calibration with dispatch optimization in a single closed-loop pipeline.
Evidence needed
- Case study comparisons: static calibration vs rolling calibration; open-loop vs closed-loop dispatch.
- Operational metrics (flood control, water supply, energy) and forecast metrics.
Falsification
- No statistically meaningful improvement over strong open-loop baselines or gains vanish under uncertainty.

Candidate 2: Dual estimation + uncertainty-aware MPC for robust dispatch
Claim (1 sentence)
- Combining dual state-parameter estimation (e.g., EnKF) with scenario-based MPC yields more reliable real-time dispatch under forecast uncertainty.
Why it matters
- Dispatch robustness depends on how forecast uncertainty is represented and updated.
What existing work covers
- EnKF-based parameter estimation; MPC for reservoir operation; forecast uncertainty-aware dispatch.
Gap
- Few studies close the loop between online parameter updates and scenario-based MPC in reservoir operations.
Evidence needed
- Ablation: MPC with fixed parameters vs dual estimation.
- Reliability/robustness metrics across hydrologic regimes.
Falsification
- MPC performance insensitive to parameter updates or degrades due to filter instability.

Candidate 3: Forecast-dispatch-implementation feedback for multi-objective tradeoffs
Claim (1 sentence)
- A feedback-aware coupling of forecast, dispatch, and implementation improves multi-objective tradeoffs (flood control vs water supply vs hydropower) compared to sequential planning.
Why it matters
- Implementation constraints and execution delays cause plan-reality gaps.
What existing work covers
- Forecast-informed reservoir operation and multi-objective optimization.
Gap
- Lack of explicit implementation-feedback modeling in real-time dispatch studies.
Evidence needed
- Models for implementation lag or execution noise.
- Sensitivity analysis to feedback delays.
Falsification
- Benefits disappear when implementation lag is modeled, or tradeoffs worsen.

Candidate 4: Rolling calibration as a guardrail against nonstationarity
Claim (1 sentence)
- Rolling calibration of inflow models reduces performance degradation under nonstationary climate or land-use shifts, leading to more stable dispatch outcomes.
Why it matters
- Nonstationarity is a dominant driver of forecast bias in long-running operations.
What existing work covers
- Time-varying parameter estimation; forecast value studies.
Gap
- Few reservoir operation papers quantify how rolling calibration stabilizes dispatch under nonstationarity.
Evidence needed
- Stress tests with regime shifts (synthetic or historical split).
- Comparison of dispatch stability metrics.
Falsification
- Rolling calibration increases variance and destabilizes operations.
