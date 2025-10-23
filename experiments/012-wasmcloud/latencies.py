#!/usr/bin/env python3

import os
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import seaborn as sns

HEALTH_STATUS = os.environ.get(
    "HEALTH_STATUS", "data/wasmcloud/dataset/health_status.csv"
)
CAPABILITIES = os.environ.get("CAPABILITIES", "data/wasmcloud/dataset/capabilities.csv")
WASM_CLOUD_LATENCIES = os.environ.get(
    "WASM_CLOUD_LATENCIES", "data/wasmcloud/latencies.csv"
)
IMAGE_TYPE = os.environ.get("IMAGE_TYPE", "pdf")

basename = os.path.basename(os.getcwd())

pd.set_option("display.show_dimensions", False)
pd.set_option("display.max_columns", None)
pd.set_option("display.max_colwidth", None)

df = pd.read_csv(WASM_CLOUD_LATENCIES)

for size in df["size"].unique():
    df.loc[df["size"] == size, "timestamp"] = (
        df.loc[df["size"] == size, "timestamp"]
        - df[df["size"] == size]["timestamp"].min()
    )

df["latency"] *= 1000.0

bin_duration = 10
df["timestamp_bin"] = (df["timestamp"] / bin_duration).apply(np.floor)

metrics = [
    ("latency", "Application latency (ms)"),
]

for y, ylabel in metrics:
    fig, ax = plt.subplots()
    sns.lineplot(
        df,
        x="timestamp_bin",
        y=y,
        hue="size",
        errorbar=("ci", 95),
        ax=ax,
        estimator="mean",
    )
    ax.set_xlabel("Time (s)")
    ax.set_ylabel(ylabel)
    ax.set_xlim(left=0.0, right=60.0)
    fig.suptitle("")
    plt.savefig("{}-{}-time.{}".format(basename, y, IMAGE_TYPE))

grouped = df.groupby(["timestamp_bin", "size"])["latency"].count().to_frame()
grouped["latency"] /= bin_duration

fig, ax = plt.subplots()
sns.lineplot(
    grouped,
    x="timestamp_bin",
    y="latency",
    hue="size",
    errorbar=("ci", 95),
    ax=ax,
    estimator="count",
)
ax.set_xlabel("Time (s)")
ax.set_ylabel("Throughput (messages/s)")
ax.set_xlim(left=0.0, right=60.0)
fig.suptitle("")
plt.savefig("{}-throughput-time.{}".format(basename, IMAGE_TYPE))
