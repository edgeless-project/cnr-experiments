#!/usr/bin/env python3

import pandas as pd
import numpy as np
import os

filename = os.environ.get("DATASET", "")
if filename == "":
    raise RuntimeError("missing environment variable DATASET")

warmup = float(os.environ.get("WARMUP", "0.1"))
assert 0 <= warmup <= 1

df = pd.read_csv(filename)
min_ts, max_ts = df["timestamp"].min(), df["timestamp"].max()
warmup_ts = min_ts + (max_ts - min_ts) * warmup
df = df[df["timestamp"] >= warmup_ts]
df["value"] = df["value"].apply(lambda x: x * 1000)

grouped = df.groupby("identifier")["value"]
grouped_ts = df.groupby("identifier")["timestamp"]
tpts = grouped_ts.count() / (grouped_ts.max() - grouped_ts.min())
tpts.replace(np.inf, np.nan, inplace=True)
print(
    "avg {:.2f}, mean-jitter {:.2f}, mean-q95 {:.2f}, q95-q95 {:.2f}, avg tpt {:.2f}".format(
        df["value"].mean(),
        (grouped.quantile(0.95) - grouped.quantile(0.05)).mean(),
        grouped.quantile(0.95).mean(),
        grouped.quantile(0.95).quantile(0.95),
        tpts.dropna().mean(),
    )
)
