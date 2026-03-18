from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Tuple


@dataclass(frozen=True)
class LSTMConfig:
    lookback_days: int
    horizon_days: int
    hidden_dim: int
    num_layers: int
    dropout: float


@dataclass
class LSTMArtifacts:
    model: Any  # torch.nn.Module
    x_mean: float
    x_std: float
    lookback_days: int


def _prep_series(y):
    """
    Stabilize inflow magnitudes via log1p.
    """
    import numpy as np

    y = np.asarray(y, dtype=float).reshape(-1)
    return np.log1p(np.maximum(y, 0.0))


def build_lstm_model(*, hidden_dim: int, num_layers: int, dropout: float):
    import torch
    import torch.nn as nn

    class _Model(nn.Module):
        def __init__(self):
            super().__init__()
            self.lstm = nn.LSTM(
                input_size=1,
                hidden_size=int(hidden_dim),
                num_layers=int(num_layers),
                dropout=float(dropout) if int(num_layers) > 1 else 0.0,
                batch_first=True,
            )
            self.head = nn.Linear(int(hidden_dim), 1)

        def forward(self, x):
            out, _ = self.lstm(x)
            last = out[:, -1, :]
            return self.head(last)

    return _Model()


def make_supervised_xy(x, *, lookback: int) -> Tuple[Any, Any]:
    import numpy as np

    x = np.asarray(x, dtype=float).reshape(-1)
    if x.shape[0] <= lookback:
        raise ValueError("Series too short for lookback.")
    n = x.shape[0] - lookback
    X = np.zeros((n, lookback, 1), dtype=float)
    y = np.zeros((n, 1), dtype=float)
    for i in range(n):
        X[i, :, 0] = x[i : i + lookback]
        y[i, 0] = x[i + lookback]
    return X, y


def train_lstm(
    *,
    inflow_train,
    inflow_tune,
    cfg: LSTMConfig,
    seed: int,
    device: str,
    epochs: int,
    batch_size: int,
    lr: float,
) -> LSTMArtifacts:
    import numpy as np
    import torch
    from torch.utils.data import DataLoader, TensorDataset

    torch.manual_seed(int(seed))
    np.random.seed(int(seed))

    x_tr = _prep_series(inflow_train)
    x_tu = _prep_series(inflow_tune)

    mean = float(np.mean(x_tr))
    std = float(np.std(x_tr) + 1e-6)
    x_tr = (x_tr - mean) / std
    x_tu = (x_tu - mean) / std

    Xtr, ytr = make_supervised_xy(x_tr, lookback=int(cfg.lookback_days))
    Xtu, ytu = make_supervised_xy(x_tu, lookback=int(cfg.lookback_days))

    ds_tr = TensorDataset(torch.tensor(Xtr, dtype=torch.float32), torch.tensor(ytr, dtype=torch.float32))
    ds_tu = TensorDataset(torch.tensor(Xtu, dtype=torch.float32), torch.tensor(ytu, dtype=torch.float32))

    dl_tr = DataLoader(ds_tr, batch_size=int(batch_size), shuffle=True)
    dl_tu = DataLoader(ds_tu, batch_size=int(batch_size), shuffle=False)

    model = build_lstm_model(hidden_dim=int(cfg.hidden_dim), num_layers=int(cfg.num_layers), dropout=float(cfg.dropout))
    model.to(device)
    opt = torch.optim.Adam(model.parameters(), lr=float(lr))
    loss_fn = torch.nn.MSELoss()

    best_state = None
    best_val = float("inf")

    for _ in range(int(epochs)):
        model.train()
        for xb, yb in dl_tr:
            xb = xb.to(device)
            yb = yb.to(device)
            opt.zero_grad()
            pred = model(xb)
            loss = loss_fn(pred, yb)
            loss.backward()
            opt.step()

        # Simple tuning loss for checkpoint selection.
        model.eval()
        with torch.no_grad():
            vals = []
            for xb, yb in dl_tu:
                xb = xb.to(device)
                yb = yb.to(device)
                pred = model(xb)
                vals.append(float(loss_fn(pred, yb).cpu().item()))
            v = float(np.mean(vals)) if vals else float("inf")
            if v < best_val:
                best_val = v
                best_state = {k: v.clone().detach().cpu() for k, v in model.state_dict().items()}

    if best_state is not None:
        model.load_state_dict(best_state)

    return LSTMArtifacts(model=model, x_mean=mean, x_std=std, lookback_days=int(cfg.lookback_days))


def lstm_multistep_forecast_mean(art: LSTMArtifacts, *, inflow_hist, horizon: int, device: str):
    """
    Recursive multi-step forecast. Uses log1p+standardization internally.
    """
    import numpy as np
    import torch

    hist = np.asarray(inflow_hist, dtype=float).reshape(-1)
    if hist.shape[0] < int(art.lookback_days):
        raise ValueError("Need at least lookback_days history.")

    x = _prep_series(hist)
    x = (x - float(art.x_mean)) / float(art.x_std)
    x = x.tolist()

    art.model.eval()
    out = np.zeros((int(horizon),), dtype=float)
    for h in range(int(horizon)):
        window = np.asarray(x[-int(art.lookback_days) :], dtype=float).reshape(1, int(art.lookback_days), 1)
        with torch.no_grad():
            pred = art.model(torch.tensor(window, dtype=torch.float32, device=device)).cpu().numpy().reshape(-1)[0]
        x.append(float(pred))
        # Invert normalization and log1p.
        pred_raw = float(pred) * float(art.x_std) + float(art.x_mean)
        out[h] = float(np.expm1(pred_raw))
    return out

