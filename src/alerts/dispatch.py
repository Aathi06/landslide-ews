"""Decide which settlements need an alert, in which languages, without repeating yourself."""
from dataclasses import dataclass
from typing import Callable, Iterable

import numpy as np

from .messages import LEVEL_RANK, alert_level, format_alert
from .telegram import send_telegram


@dataclass(frozen=True)
class SentAlert:
    village: str
    level: str
    lang: str
    text: str
    delivered: bool


class AlertTracker:
    """Remembers the highest level already announced per settlement.
    A settlement is only alerted again if its level goes UP (watch -> warning -> emergency)."""

    def __init__(self) -> None:
        self._sent: dict[str, int] = {}

    def should_send(self, village: str, level: str) -> bool:
        return LEVEL_RANK[level] > self._sent.get(village, 0)

    def mark(self, village: str, level: str) -> None:
        self._sent[village] = max(LEVEL_RANK[level], self._sent.get(village, 0))


def dispatch_alerts(villages: Iterable, risk_frame: np.ndarray, tracker: AlertTracker,
                    langs: tuple[str, ...] = ("en", "ta"),
                    send: Callable[[str], bool] = send_telegram) -> list[SentAlert]:
    """villages: objects with .name .pop .cell (see src.exposure.villages.Village).
    risk_frame: uint8 array 0..100 indexed by cell. Returns what was announced this call.
    A settlement is marked as announced even if delivery failed or Telegram is unconfigured (dry run),
    so a missing token never causes a flood of repeats."""
    out: list[SentAlert] = []
    for v in villages:
        risk = float(risk_frame[v.cell]) / 100
        level = alert_level(risk)
        if level is None or not tracker.should_send(v.name, level):
            continue
        for lang in langs:
            text = format_alert(v.name, risk, v.pop, lang)
            out.append(SentAlert(v.name, level, lang, text, send(text)))
        tracker.mark(v.name, level)
    return out
