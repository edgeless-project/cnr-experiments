#!/usr/bin/env python3

import pandas as pd
from pandas.api.types import is_numeric_dtype
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

for col in df.columns:
    if is_numeric_dtype(df[col]):
        print(
            "{}: min {} max {} avg {} +- {}".format(
                col, df[col].min(), df[col].max(), df[col].mean(), df[col].std()
            )
        )
