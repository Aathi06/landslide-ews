import numpy as np
import pytest

from src.alerts import telegram
from src.alerts.dispatch import AlertTracker, dispatch_alerts
from src.alerts.messages import LEVEL_RANK, SUPPORTED_LANGS, TEMPLATES, alert_level, format_alert
from src.exposure.villages import Village


def test_levels():
    assert alert_level(0.2) is None
    assert alert_level(0.5) == "watch"
    assert alert_level(0.7) == "warning"
    assert alert_level(0.9) == "emergency"


def test_every_language_has_every_level():
    for lang in SUPPORTED_LANGS:
        assert set(TEMPLATES[lang]) == set(LEVEL_RANK)
        for level in LEVEL_RANK:
            text = TEMPLATES[lang][level].format(village="X", risk=80, people="1,000")
            assert "X" in text and "80" in text and "1,000" in text


def test_format_alert():
    assert format_alert("Kotagiri", 0.3, 100) is None
    en = format_alert("Kotagiri", 0.74, 3206, "en")
    assert "Kotagiri" in en and "74%" in en and "3,206" in en
    assert "Kotagiri" in format_alert("Kotagiri", 0.9, 10, "ta")
    with pytest.raises(ValueError):
        format_alert("Kotagiri", 0.9, 10, "fr")


def make_villages():
    return [Village("A", 1000, 0, 0, 0), Village("B", 500, 1, 0, 0), Village("C", 50, 2, 0, 0)]


def test_dispatch_sends_once_and_only_on_escalation():
    sent = []
    send = lambda text: sent.append(text) or True
    tracker, vs = AlertTracker(), make_villages()
    first = dispatch_alerts(vs, np.array([75, 20, 55], dtype=np.uint8), tracker, langs=("en", "ta"), send=send)
    assert {(a.village, a.level) for a in first} == {("A", "warning"), ("C", "watch")}
    assert len(first) == 4 and all(a.delivered for a in first)          # 2 villages x 2 languages
    assert dispatch_alerts(vs, np.array([75, 20, 55], dtype=np.uint8), tracker, send=send) == []   # no repeats
    again = dispatch_alerts(vs, np.array([90, 20, 55], dtype=np.uint8), tracker, langs=("en",), send=send)
    assert [(a.village, a.level) for a in again] == [("A", "emergency")]  # escalation re-alerts


def test_telegram_dry_run_and_success(monkeypatch):
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)
    assert telegram.send_telegram("hi") is False                       # not configured

    class FakeResp:
        status_code = 200
        def json(self): return {"ok": True}
    monkeypatch.setattr(telegram.httpx, "post", lambda *a, **k: FakeResp())
    assert telegram.send_telegram("hi", token="t", chat_id="c") is True
