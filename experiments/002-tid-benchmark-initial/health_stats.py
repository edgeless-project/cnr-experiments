#!/usr/bin/env python3

import pandas as pd
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

for metric in ["load_avg_1"]:
    print("metric: {}".format(metric))
    grouped = df.groupby("node_id")[metric]
    print(grouped.describe())
