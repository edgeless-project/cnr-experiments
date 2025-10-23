#!/usr/bin/env python3

import os
import pandas as pd
import numpy as np
from common import plot_node_health, load_node_names

HEALTH_STATUS = os.environ.get(
    "HEALTH_STATUS", "data/wasmcloud/dataset/health_status.csv"
)
CAPABILITIES = os.environ.get("CAPABILITIES", "data/wasmcloud/dataset/capabilities.csv")
WASM_CLOUD_LATENCIES = os.environ.get(
    "WASM_CLOUD_LATENCIES", "data/wasmcloud/latencies.csv"
)


df = pd.read_csv(WASM_CLOUD_LATENCIES)
time_ranges = []
for size in df["size"].unique():
    time_ranges.append(
        (
            df[df["size"] == size].min().timestamp,
            df[df["size"] == size].max().timestamp,
            size,
        )
    )

df = pd.read_csv(HEALTH_STATUS)

df.replace(load_node_names(CAPABILITIES), inplace=True)

plot_node_health(df, "wasmcloud", time_ranges)
