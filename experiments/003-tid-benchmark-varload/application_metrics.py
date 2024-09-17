#!/usr/bin/env python3

import pandas as pd
import os
import matplotlib.pyplot as plt

filename = os.environ.get("DATASET", "")
if filename == "":
    raise RuntimeError("missing environment variable DATASET")

warmup = float(os.environ.get("WARMUP", "0.1"))
assert 0 <= warmup <= 1

df = pd.read_csv(filename)
df = df[df["entity"] == "w"]
min_ts, max_ts = df["timestamp"].min(), df["timestamp"].max()
warmup_ts = min_ts + (max_ts - min_ts) * warmup
df = df[df["timestamp"] >= warmup_ts]

for orchestration in df["orchestration"].unique():
    grouped = (
        df[df["orchestration"] == orchestration]
        .groupby(["orchestration", "interarrival", "seed", "name"])["value"]
        .quantile(0.95)
        .groupby(["interarrival"])
        .mean()
    )
    grouped.plot(label=orchestration)
plt.ylabel("Average 95th percentile of workflow latency")
plt.xlabel("Average interarrival between workflows (s)")
plt.grid()
plt.legend()
plt.show()
