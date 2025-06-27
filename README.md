# Adaptive Checkpointer

[![PyPI Version](https://img.shields.io/pypi/v/adaptive-checkpointer)](https://pypi.org/project/adaptive-checkpointer)
[![Documentation Status](https://github.com/Straussberg/adaptive-checkpointer/actions/workflows/docs.yml/badge.svg)](https://Straussberg.github.io/adaptive-checkpointer)
[![Test Status](https://github.com/Straussberg/adaptive-checkpointer/actions/workflows/ci.yml/badge.svg)](https://github.com/Straussberg/adaptive-checkpointer/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> √T-based adaptive checkpointing system for large-scale distributed simulations.

## Features

- Sublinear memory usage (O(√T))
- Tiered storage: RAM → Disk → S3
- Adaptive rollback handling
- Works with OMNeT++, NS-3, or standalone

## Quick Start

```bash
pip install adaptive-checkpointer

from adaptive_checkpointer import AdaptiveCheckpointer

cp = AdaptiveCheckpointer(base_interval=500)
state = {"counter": 0}

for event in range(100_000):
    state["counter"] += event
    if cp.should_checkpoint(event):
        cp.save_checkpoint(event, state)


