#!/usr/bin/env python3

import pandas as pd
import os

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

grouped = df.groupby("name")["value"]
grouped_ts = df.groupby("name")["value"]
print(
    "avg {:.2f}, mean-jitter {:.2f}, mean-q95 {:.2f}, q95-q95 {:.2f}, tpt {:.2f}".format(
        df["value"].mean(),
        (grouped.quantile(0.95) - grouped.quantile(0.05)).mean(),
        grouped.quantile(0.95).mean(),
        grouped.quantile(0.95).quantile(0.95),
        (grouped.count() / (grouped_ts.max() - grouped_ts.min())).mean(),
    )
)
