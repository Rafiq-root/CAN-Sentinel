"""Tests for per-vehicle critical-ID profiles (alerts/severity_rules.py)."""
import pytest

from alerts import severity_rules
from alerts.dashboard_feed import dashboard_payload
from alerts.manager import AlertManager
from alerts.replay_gem import main as replay_main
from alerts.severity_rules import (CRITICAL_CAN_IDS,
                                   set_vehicle_critical_map)


@pytest.fixture(autouse=True)
def restore_mock_profile():
    yield
    set_vehicle_critical_map("mock_vehicle")   # no test leaks global state


def _ev(can_id, rule="UNKNOWN_ID", ts="2026-10-31T10:00:00Z"):
    return {"can_id": can_id, "rule": rule, "timestamp": ts}


def test_unknown_profile_raises_loud():
    with pytest.raises(ValueError):
        set_vehicle_critical_map("tesla_model_s")


def test_gem_ids_escalate_only_under_gem_map():
    m = AlertManager()
    m.process_event(_ev("0x18FF00F9"))            # UNKNOWN_ID: MEDIUM base
    assert m.get_alerts()[0]["severity"] == "MEDIUM"          # mock profile
    set_vehicle_critical_map("gem_e6")
    m2 = AlertManager()
    m2.process_event(_ev("0x18FF00F9"))
    assert m2.get_alerts()[0]["severity"] == "HIGH"           # gem profile


def test_swap_is_real_mock_only_id_de_escalates():
    set_vehicle_critical_map("gem_e6")
    m = AlertManager()
    m.process_event(_ev("0x1A4"))                 # mock-only critical ID
    assert m.get_alerts()[0]["severity"] == "MEDIUM"   # no longer critical


def test_same_imported_object_is_mutated_in_place():
    obj_id = id(CRITICAL_CAN_IDS)
    set_vehicle_critical_map("gem_e6")
    assert id(severity_rules.CRITICAL_CAN_IDS) == obj_id
    assert "0x18FF00F9" in CRITICAL_CAN_IDS
    assert "0x1A4" not in CRITICAL_CAN_IDS


def test_panel_reflects_swap_built_after_it():
    m = AlertManager()
    m.process_event(_ev("0x18FF70F9"))
    assert dashboard_payload(m)["critical_active"] == []       # mock: empty
    set_vehicle_critical_map("gem_e6")
    panel = dashboard_payload(m)["critical_active"]            # rebuilt after
    assert [r["can_id"] for r in panel] == ["0x18FF70F9"]      # gem: listed


def test_panel_reflects_swap_back():
    set_vehicle_critical_map("gem_e6")
    m = AlertManager()
    m.process_event(_ev("0x18FF70F9"))
    set_vehicle_critical_map("mock_vehicle")
    assert dashboard_payload(m)["critical_active"] == []


def test_cli_vehicle_flag_end_to_end(tmp_path, capsys):
    csv = tmp_path / "gem.csv"
    csv.write_text(
        "timestamp,arbitration_id,dlc,data0,data1,data2,data3,data4,"
        "data5,data6,data7,label,Attack_Type\r\n"
        "8.769,18FF00F9,8,5,0,C5,85,FA,FF,7A,0,1,Brake Tampering\r\n")
    rc = replay_main([str(csv), "--vehicle", "gem_e6"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "alerts=1" in out
    triage = out.split("Critical IDs")[1].split("##")[0]
    assert "0x18FF00F9" in triage          # the finding, closed
