#!/usr/bin/env python3

import os
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import seaborn as sns

HEALTH_STATUS = os.environ.get("HEALTH_STATUS", "data/wasmcloud/dataset/health_status.csv")
CAPABILITIES = os.environ.get("CAPABILITIES", "data/wasmcloud/dataset/capabilities.csv")
WASM_CLOUD_LATENCIES = os.environ.get("WASM_CLOUD_LATENCIES", "data/wasmcloud/latencies.csv")
IMAGE_TYPE = os.environ.get("IMAGE_TYPE", "pdf")

basename = os.path.basename(os.getcwd())

pd.set_option("display.show_dimensions", False)
pd.set_option("display.max_columns", None)
pd.set_option("display.max_colwidth", None)

df = pd.read_csv(WASM_CLOUD_LATENCIES)

for size in df["size"].unique():
    df.loc[df["size"] == size, "timestamp"] = df.loc[df["size"] == size, "timestamp"] - df[df["size"] == size]["timestamp"].min()

df["latency"] *= 1000.0

metrics = [
    ("latency", "Application latency (ms)"),
]

for y, ylabel in metrics:
    fig, ax = plt.subplots()
    sns.lineplot(df, x="timestamp", y=y, hue="size",ax=ax)
    ax.set_xlabel("Time (s)")
    ax.set_ylabel(ylabel)
    fig.suptitle("")
    plt.savefig("{}-{}-time.{}".format(basename,y, IMAGE_TYPE))
