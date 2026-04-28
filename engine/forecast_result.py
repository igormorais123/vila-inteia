"""Typed result for combined forecast pipeline."""

from __future__ import annotations

from dataclasses import dataclass, asdict


@dataclass(frozen=True)
class ForecastResult:
    n: int
    base_acc: float
    base_brier: float
    bootstrap_brier_ci: tuple[float, float]
    selective: dict[float, dict]
    conformal: dict
    murphy: dict
    time_series_cv: dict

    def as_dict(self) -> dict:
        """Backward-compat dict view."""
        return {
            "n": self.n,
            "base_acc": self.base_acc,
            "base_brier": self.base_brier,
            "bootstrap_brier_ci": self.bootstrap_brier_ci,
            "selective": self.selective,
            "conformal": self.conformal,
            "murphy": self.murphy,
            "time_series_cv": self.time_series_cv,
        }

    def __getitem__(self, key: str):
        """Subscript access for backward compat with dict callers."""
        return self.as_dict()[key]

    def __contains__(self, key: str) -> bool:
        return key in self.as_dict()
