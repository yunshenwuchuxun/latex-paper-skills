# Outline Contract

Assumed mode: empirical method + case study (confirm with user).

Section plan and intent
1. Introduction
- Problem: real-time reservoir operation depends on inflow forecasts that drift under nonstationarity.
- Gap: forecast-informed operation rarely integrates rolling parameter calibration and closed-loop feedback.
- Contributions: C1-C4.
- Target citations: 8
- Figures/tables: 0

2. Background and related work
- Inflow forecasting methods and uncertainty quantification.
- Rolling parameter estimation and data assimilation in hydrology.
- Forecast-informed reservoir operation and MPC.
- Target citations: 20
- Figures/tables: 1 (taxonomy or pipeline summary)

3. Problem formulation
- System, objectives, constraints, decision horizon, and data cadence.
- Define operational metrics and forecast metrics.
- Target citations: 2
- Figures/tables: 1 (notation table)

4. Methodology
4.1 Rolling parameter calibration module
- Estimation method (e.g., dual EnKF or sliding-window calibration).
- Inputs/outputs and update frequency.
- Target citations: 4
- Figures/tables: 1 (module diagram)

4.2 Inflow forecasting module
- Model class (hydrological or ML) and uncertainty representation.
- Target citations: 4
- Figures/tables: 1 (forecasting pipeline)

4.3 Dispatch optimization module
- MPC or stochastic optimization using forecast ensembles.
- Target citations: 4
- Figures/tables: 1 (optimization formulation)

4.4 Closed-loop coupling algorithm
- End-to-end cycle: observe -> calibrate -> forecast -> dispatch -> implement -> feedback.
- Target citations: 2
- Figures/tables: 1 (closed-loop workflow)

5. Case study and data
- Reservoir description, objectives, constraints, and data sources.
- Target citations: 2
- Figures/tables: 1 (map or system diagram)

6. Experimental design and baselines
- Baselines: static calibration + open-loop, rolling calibration + open-loop, deterministic vs ensemble dispatch.
- Evaluation metrics and statistical testing.
- Target citations: 4
- Figures/tables: 2 (baseline table, metric definitions)

7. Results
7.1 Forecast accuracy and uncertainty calibration
- Metrics and seasonal breakdowns.
- Figures/tables: 2

7.2 Operational performance
- Reliability, resiliency, vulnerability, spill/deficit metrics.
- Figures/tables: 2

7.3 Sensitivity and robustness
- Nonstationarity stress tests and parameter sensitivity.
- Figures/tables: 1

8. Discussion
- Practical deployment considerations and limitations.
- Target citations: 2
- Figures/tables: 0

9. Conclusion
- Summary of findings and next steps.
- Target citations: 0
- Figures/tables: 0

Figure budget (target): 8-10 total
Table budget (target): 3-4 total
