import pytest
from adaptive_checkpointer.core import AdaptiveCheckpointer

def test_checkpoint_decision():
    ckpt = AdaptiveCheckpointer(base_interval=100)
    state = {"event": 100, "value": "test"}
    ckpt.save_checkpoint(100, state)
    ev, recovered = ckpt.get_last_checkpoint(150)
    assert ev == 100
    assert recovered["event"] == 100
    assert recovered["value"] == "test"

def test_rollback_recording():
    ckpt = AdaptiveCheckpointer(base_interval=100)
    ckpt.record_rollback(80)
    ckpt.record_rollback(120)
    ckpt.record_rollback(60)
    assert len(ckpt.rollback_depths) == 3
    assert max(ckpt.rollback_depths) == 120
