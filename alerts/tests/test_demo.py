"""Tests for the mid-review demo script (alerts/demo.py)."""
from alerts.demo import run_demo


def test_demo_shows_folding_escalation_rejection():
    report = run_demo()
    assert "occurrences=10" in report      # 10 DoS events folded into 1 alert
    assert "severity HIGH" in report       # DoS + airbag escalation
    assert "rejected=1" in report          # int can_id rejected, not crashed
    assert "alerts=2" in report            # both real alerts survived


def test_demo_emits_render_ready_dashboard_payload():
    report = run_demo()
    assert "critical_active" in report     # triage panel present
    assert "by_severity" in report         # summary block present
    assert "ACKNOWLEDGED" in report        # lifecycle state visible to M4
