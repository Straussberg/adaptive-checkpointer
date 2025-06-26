import tempfile
import os
from adaptive_checkpointer.backends import MemoryStorage, DiskStorage

def test_memory_storage():
    backend = MemoryStorage()
    backend.save(42, b"checkpoint-data")
    assert backend.load(42) == b"checkpoint-data"
    assert backend.load(99) == b''  # evento inexistente

def test_disk_storage():
    with tempfile.TemporaryDirectory() as tmpdir:
        backend = DiskStorage(directory=tmpdir)
        backend.save(17, b"disk-checkpoint")
        assert backend.load(17) == b"disk-checkpoint"
        assert backend.load(123456) == b''  # inexistente
