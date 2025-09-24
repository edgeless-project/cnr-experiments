#!/usr/bin/env python3

import os
import matplotlib.pyplot as plt
import seaborn as sns
from utils import load_dataset, show_or_save

HEALTH_STATUS = os.environ.get("HEALTH_STATUS", "dataset/health_status.csv")
SHOW = bool(os.environ.get("SHOW", ""))
MIN_TIMESTAMP = float(os.environ.get("MIN_TIMESTAMP", "200"))
MAX_TIMESTAMP = float(os.environ.get("MAX_TIMESTAMP", "900"))

basename = os.path.basename(os.getcwd())

df = load_dataset(
    HEALTH_STATUS, min_timestamp=MIN_TIMESTAMP, max_timestamp=MAX_TIMESTAMP
)

df["mem_occupancy"] = (df["mem_used"] / df["mem_available"]) * 100

df["rx_throughput"] = df.groupby(["seed", "node_id"])["tot_rx_bytes"].diff()
df["tx_throughput"] = df.groupby(["seed", "node_id"])["tot_rx_bytes"].diff()
df["interval"] = df.groupby(["seed", "node_id"])["timestamp"].diff()
df["tot_throughput"] = (df["rx_throughput"] + df["tx_throughput"]) / (
    df["interval"] * 1048576
)
# df.timestamp *= 1 / 3600.0

match = "orin-"
df.drop(df[~df.node_id.str.contains(match)].index, inplace=True)
df.replace({"node_id": {match: ""}}, inplace=True, regex=True)

metrics = [
    ("proc_cpu_usage", "Process CPU usage"),
    ("mem_occupancy", "Memory occupancy"),
    ("tot_throughput", "Network traffic per node (Mb/s)"),
    ("active_power", "Active power (mW)"),
]

for y, ylabel in metrics:
    fig, ax = plt.subplots()
    sns.lineplot(df, x="timestamp", y=y, hue="node_id", ax=ax, legend=False)
    ax.set_xlabel("Time (s)")
    ax.set_ylabel(ylabel)
    fig.suptitle("")
    show_or_save("{}-{}-time".format(basename, y))

if SHOW:
    input("Press any key to continue")
