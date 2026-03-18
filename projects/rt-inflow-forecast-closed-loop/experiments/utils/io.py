from __future__ import annotations

import csv
from pathlib import Path
from typing import Any


def append_csv_row(*, results_path: Path, header: list[str], row_dict: dict[str, Any]) -> None:
    results_path.parent.mkdir(parents=True, exist_ok=True)
    exists = results_path.exists()
    with results_path.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=header)
        if not exists:
            writer.writeheader()
        writer.writerow({k: row_dict.get(k, "") for k in header})


