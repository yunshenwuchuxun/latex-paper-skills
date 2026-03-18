# Topic Brief

Topic (working English translation)
- Rolling calibration of inflow-forecast model parameters for real-time forecast-driven scheduling, and a closed-loop coupling method for forecast-dispatch-implementation.

Problem framing
- Real-time reservoir operation depends on short-term inflow forecasts that degrade under nonstationary conditions.
- Dispatch decisions made on stale or biased forecasts can amplify operational risk.
- A closed-loop workflow that updates forecast-model parameters and dispatch decisions after implementation can improve robustness.

Scope
- Short-term (hours to days) inflow forecasting for reservoir/hydropower operations.
- Rolling or online parameter estimation for hydrological or ML-based inflow models.
- Forecast-informed scheduling/dispatch (e.g., MPC, stochastic or rule-based optimization).
- Closed-loop coupling of forecast, dispatch, and implementation feedback.

Out of scope (unless user requests)
- Long-term climate change impacts and seasonal planning.
- New deep learning architectures unrelated to operational coupling.
- Multi-basin policy or institutional governance.

Target audience / venue type (assumed)
- Water resources / hydrology / reservoir operations research.
- Journals or conferences that accept method + case study empirical evaluation.

Constraints (TBD)
- Data availability and reservoir case study (unknown).
- Required language (assumed English for arXiv-style paper).
- Page target (assumed 8-12 pages IEEEtran two-column).

Keywords (seed)
- Reservoir inflow forecasting
- Real-time reservoir operation
- Forecast-informed scheduling
- Rolling parameter calibration
- Data assimilation
- Ensemble Kalman filter (EnKF)
- Model predictive control (MPC)
- Closed-loop operation
- Forecast uncertainty

Questions to confirm with user
- Preferred language for the paper (English or Chinese).
- Do you have a target reservoir / dataset and operational objectives?
- Do you want a novel empirical method (with experiments) or a review/synthesis paper?
- Any constraints on tools, baselines, or evaluation metrics?

Assumptions for now
- Empirical method paper with at least one case study.
- Focus on short-term operational performance (flood control + water supply or hydropower).
