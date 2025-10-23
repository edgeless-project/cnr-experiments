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


def load_node_names(capabilities: str):
    df = pd.read_csv(capabilities)
    ret = dict()
    for _id, node_id, labels in df[["node_id", "labels"]].itertuples():
        labels = str(labels).replace("[", "").replace("]", "").split(";")
        hostname = node_id
        for label in labels:
            if "hostname=" in label:
                (_token, hostname) = label.split("=")
        ret[node_id] = hostname
    return ret


basename = os.path.basename(os.getcwd())

pd.set_option("display.show_dimensions", False)
pd.set_option("display.max_columns", None)
pd.set_option("display.max_colwidth", None)

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

df["mem_occupancy"] = (df["mem_used"] / df["mem_available"]) * 100

df["rx_throughput"] = df.groupby(["seed", "node_id"])["tot_rx_bytes"].diff()
df["tx_throughput"] = df.groupby(["seed", "node_id"])["tot_rx_bytes"].diff()
df["interval"] = df.groupby(["seed", "node_id"])["timestamp"].diff()
df["tot_throughput"] = (df["rx_throughput"] + df["tx_throughput"]) / (
    df["interval"] * 1048576
)
# df.timestamp *= 1 / 3600.0

# select only some nodes
match = "rpi-"
df.drop(df[~df.node_id.str.contains(match)].index, inplace=True)
df.replace({"node_id": {match: ""}}, inplace=True, regex=True)

# add experiment labels
df["experiment"] = ""
for i, row in df.iterrows():
    for time_range in time_ranges:
        (begin, end, experiment) = time_range
        begin = float(begin)
        end = float(end)
        if row["timestamp"] >= begin and row["timestamp"] <= end:
            df.at[i, "experiment"] = experiment
            break
df.replace(
    {
        "experiment": {
            "": np.nan,
        }
    },
    inplace=True,
)
df.dropna(subset=["experiment"], inplace=True)

for experiment in df["experiment"].unique():
    df.loc[df["experiment"] == experiment, "timestamp"] = (
        df.loc[df["experiment"] == experiment, "timestamp"]
        - df[df["experiment"] == experiment]["timestamp"].min()
    )

bin_duration = 10
df["timestamp_bin"] = (df["timestamp"] / bin_duration).apply(np.floor)

metrics = [
    ("load_avg_1", "Average load"),
    ("mem_occupancy", "Memory occupancy"),
    ("tot_throughput", "Network traffic per node (Mb/s)"),
]

for y, ylabel in metrics:
    fig, ax = plt.subplots()
    sns.lineplot(
        df,
        x="timestamp_bin",
        y=y,
        hue="experiment",
        errorbar=("ci", 95),
        ax=ax,
        estimator="mean",
    )
    ax.set_xlabel("Time (s)")
    ax.set_xlim(left=0.0, right=60.0)
    ax.set_ylabel(ylabel)
    fig.suptitle("")
    plt.savefig("{}-{}-time.{}".format(basename, y, IMAGE_TYPE))
