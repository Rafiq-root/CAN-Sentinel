"""Tests for the GEM ground-truth replay driver (alerts/replay_gem.py)."""
import io

from alerts.replay_gem import replay
from alerts.report import build_report

HEADER = ("timestamp,arbitration_id,dlc,data0,data1,data2,data3,"
          "data4,data5,data6,data7,label,Attack_Type")
DOS = "8.209,0,8,5,0,64,5B,0A,0,FF,0,1,DoS"
BRAKE = "8.769,18FF00F9,8,5,0,C5,85,FA,FF,7A,0,1,Brake Tampering"
STEER = "9.100,18FF70F9,8,5,0,11,22,33,44,55,0,1,Steering Tampering"
NORMAL = "30060.459,18FF7113,8,EB,D6,FA,FF,36,BF,FA,FF,0,Normal"


def _csv(rows, header=HEADER, crlf=True):
    sep = "\r\n" if crlf else "\n"
    return io.StringIO(sep.join([header] + rows) + sep)


def test_dos_row_becomes_high_frequency_high():
    m, fed, row_rej, mgr_rej = replay(_csv([DOS]))
    assert (fed, row_rej, mgr_rej) == (1, 0, 0)
    a = m.get_alerts()[0]
    assert a["can_id"] == "0x000"
    assert a["source_rule"] == "HIGH_FREQUENCY"      # adapter aliased the M2 reason
    assert a["severity"] == "HIGH"
    assert a["raw_details"]["dataset_label"] == "DoS"


def test_brake_tampering_becomes_spoofed_id_high():
    m, *_ = replay(_csv([BRAKE]))
    a = m.get_alerts()[0]
    assert a["can_id"] == "0x18FF00F9"
    assert a["source_rule"] == "SPOOFED_ID"
    assert a["severity"] == "HIGH"


def test_steering_tampering_becomes_spoofed_id_high():
    m, *_ = replay(_csv([STEER]))
    assert m.get_alerts()[0]["can_id"] == "0x18FF70F9"


def test_normal_rows_are_skipped():
    m, fed, *_ = replay(_csv([NORMAL]))
    assert fed == 0
    assert len(m.get_alerts()) == 0


def test_file_without_attack_column_is_all_clean():
    plain = HEADER.replace(",Attack_Type", "")   # normal-file shape
    m, fed, *_ = replay(_csv(
        ["127876.661,18FF00F9,8,5,0,4C,C3,FD,FF,FF,0,0"], header=plain))
    assert fed == 0


def test_crlf_endings_do_not_leak_into_fields():
    m, *_ = replay(_csv([BRAKE], crlf=True))
    d = m.get_alerts()[0]["raw_details"]
    assert d["dataset_label"] == "Brake Tampering"    # no trailing \r
    assert d["data_bytes"] == ["5", "0", "C5", "85", "FA", "FF", "7A", "0"]


def test_bad_rows_rejected_pipeline_alive():
    bad_id = "8.209,ZZZ,8,5,0,64,5B,0A,0,FF,0,1,DoS"     # unhexable arbitration_id
    bad_ts = ",0,8,5,0,64,5B,0A,0,FF,0,1,DoS"            # empty timestamp
    m, fed, row_rej, mgr_rej = replay(_csv([bad_id, bad_ts, DOS]))
    assert (fed, row_rej, mgr_rej) == (1, 2, 0)
    assert len(m.get_alerts()) == 1        # the good DoS row survived


def test_dedupe_folds_flood_within_window():
    rows = ["8.00%d,0,8,5,0,64,5B,0A,0,FF,0,1,DoS" % i for i in range(5)]
    m, fed, *_ = replay(_csv(rows))
    assert fed == 5
    alerts = m.get_alerts()
    assert len(alerts) == 1
    assert alerts[0]["occurrences"] == 5


def test_base_anchors_capture_relative_clock():
    m, *_ = replay(_csv([DOS]), timestamp_base=1793318400.0)
    assert m.get_alerts()[0]["timestamp"].startswith("2026-10-30")


def test_report_from_replayed_session():
    m, *_ = replay(_csv([DOS, BRAKE, STEER, NORMAL]))
    r = build_report(m, title="replay")
    assert "Total alerts: 3" in r
    assert "0x000" in r and "0x18FF00F9" in r
