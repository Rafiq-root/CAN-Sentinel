import unittest
import pandas as pd
from can_ids.engine import DetectionEngine, EngineConfig
from can_ids.preprocess import parse_can_id, parse_payload, validate_can_dataframe

class TestCanIDS(unittest.TestCase):
    def test_parse_can_id(self):
        self.assertEqual(parse_can_id("0x123"), 0x123)
        self.assertEqual(parse_can_id("291"), 291)

    def test_parse_payload(self):
        self.assertEqual(parse_payload("1122AABB"), [0x11, 0x22, 0xAA, 0xBB])
        self.assertEqual(parse_payload("11 22 AA BB"), [0x11, 0x22, 0xAA, 0xBB])

    def test_rate_detection(self):
        df = pd.DataFrame({
            "timestamp": [0.0, 0.01, 0.02, 0.03],
            "can_id": [0x123] * 4,
            "dlc": [1] * 4,
            "data_bytes": [[1], [1], [1], [1]],
            "label": ["normal"] * 4,
        })
        engine = DetectionEngine(EngineConfig(max_messages_per_id_per_window=2, suspicious_payload_repeat_count=100))
        result = engine.process_dataframe(df)
        self.assertTrue(result["is_alert"].any())
        self.assertIn("CAN_ID_RATE_EXCEEDED", ";".join(result["reasons"]))

    def test_no_rate_alert_below_threshold(self):
        df = pd.DataFrame({
            "timestamp": [0.0, 2.0, 4.0],
            "can_id": [0x123] * 3,
            "dlc": [1] * 3,
            "data_bytes": [[1], [2], [3]],
            "label": ["normal"] * 3,
        })
        engine = DetectionEngine(EngineConfig(max_messages_per_id_per_window=5, suspicious_payload_repeat_count=100))
        result = engine.process_dataframe(df)
        self.assertFalse(result["is_alert"].any())

if __name__ == "__main__":
    unittest.main()
