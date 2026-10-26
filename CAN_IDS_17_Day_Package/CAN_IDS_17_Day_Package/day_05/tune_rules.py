from can_ids.engine import EngineConfig
# Starting values only. Tune against known-normal validation traffic.
config = EngineConfig(
    window_seconds=1.0,
    max_messages_per_id_per_window=100,
    max_global_messages_per_window=2000,
    suspicious_payload_repeat_count=30,
)
print(config)
