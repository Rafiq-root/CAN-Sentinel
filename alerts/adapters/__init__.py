"""Integration adapters: teammate module output -> M3 alert event contract."""
from .from_m2 import RULE_ALIASES, ingest_rows, translate_rows

__all__ = ["RULE_ALIASES", "ingest_rows", "translate_rows"]
