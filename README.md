# Adaptive Checkpointer [![PyPI](https://img.shields.io/pypi/v/adaptive-checkpointer)](https://pypi.org/project/adaptive-checkpointer/)

> √T-based adaptive checkpointing for distributed simulations and systems

```python
from adaptive_checkpointer import AdaptiveCheckpointer, TieredBackend

backend = TieredBackend().add_ram_layer(10000) \
                         .add_nvme_layer(100000, "/mnt/pmem") \
                         .add_s3_layer("my-bucket")

checkpointer = AdaptiveCheckpointer(
    base_interval=500,
    storage=backend,
    metrics=True
)# adaptive-checkpointer
