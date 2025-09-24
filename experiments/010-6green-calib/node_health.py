#!/usr/bin/env python3

import os
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from utils import load_dataset, show_or_save, relabel

HEALTH_STATUS = os.environ.get("HEALTH_STATUS", "data/dataset/health_status.csv")
CAPABILITIES = os.environ.get("CAPABILITIES", "data/dataset/capabilities.csv")
SHOW = bool(os.environ.get("SHOW", ""))

basename = os.path.basename(os.getcwd())

df = load_dataset(HEALTH_STATUS, CAPABILITIES, min_timestamp=None, max_timestamp=None)

df["mem_occupancy"] = (df["mem_used"] / df["mem_available"]) * 100

df["rx_throughput"] = df.groupby(["seed", "node_id"])["tot_rx_bytes"].diff()
df["tx_throughput"] = df.groupby(["seed", "node_id"])["tot_rx_bytes"].diff()
df["interval"] = df.groupby(["seed", "node_id"])["timestamp"].diff()
df["tot_throughput"] = (df["rx_throughput"] + df["tx_throughput"]) / (
    df["interval"] * 1048576
)
# df.timestamp *= 1 / 3600.0

time_range = []
with open("workflow-ranges.csv", "r") as infile:
    for line in infile:
        time_range.append(line.rstrip().split(","))

df["experiment"] = ""
df["size"] = ""
df["num_workflows"] = 0

for i, row in df.iterrows():
    for trange in time_range:
        (begin, end, experiment, size, num_workflows) = trange
        begin = float(begin)
        end = float(end)
        if row["timestamp_abs"] >= begin and row["timestamp_abs"] <= end:
            df.at[i, "experiment"] = experiment
            df.at[i, "size"] = size
            df.at[i, "num_workflows"] = int(num_workflows)
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

df.drop(
    df[~df.node_id.str.contains("orin-") & ~df.node_id.str.contains("rpi-")].index,
    inplace=True,
)

conditions = [df.node_id.str.contains("orin-"), df.node_id.str.contains("rpi-")]
choices = ["orin", "rpi"]
df["node"] = np.select(conditions, choices, default="unknown")
assert set(["orin", "rpi"]) == set(df.node.unique())

relabel(df)

metrics = [
    ("proc_cpu_usage", "Process CPU usage"),
    ("mem_occupancy", "Memory occupancy"),
    ("tot_throughput", "Network traffic per node (Mb/s)"),
    ("active_power", "Active power (mW)"),
]

order = [
    "rpi-1k",
    "rpi-10k",
    "rpi-100k",
    "rpi-1M",
    "orin-1k",
    "orin-10k",
    "orin-100k",
    "orin-1M",
]
for y, ylabel in metrics:
    fig, ax = plt.subplots()
    sns.boxplot(df, x="label", y=y, hue="num_workflows", ax=ax, order=order)
    ax.set_ylabel(ylabel)
    plt.xticks(rotation=45)
    fig.suptitle("")
    show_or_save("{}-{}".format(basename, y))

if SHOW:
    input("Press any key to continue")
