#!/usr/bin/env python3

import os
import matplotlib.pyplot as plt
import seaborn as sns
from utils import load_dataset, show_or_save

HEALTH_STATUS = os.environ.get("HEALTH_STATUS", "dataset/health_status.csv")
SHOW = bool(os.environ.get("SHOW", ""))
BOX = bool(os.environ.get("BOX", ""))
TIME = bool(os.environ.get("TIME", ""))
MATCH = os.environ.get("MATCH", "")

basename = os.path.basename(os.getcwd())

df = load_dataset(HEALTH_STATUS, min_timestamp=None, max_timestamp=None)

df["mem_occupancy"] = (df["mem_used"] / df["mem_available"]) * 100

df["rx_throughput"] = df.groupby(["seed", "node_id"])["tot_rx_bytes"].diff()
df["tx_throughput"] = df.groupby(["seed", "node_id"])["tot_rx_bytes"].diff()
df["interval"] = df.groupby(["seed", "node_id"])["timestamp"].diff()
df["tot_throughput"] = (df["rx_throughput"] + df["tx_throughput"]) / (
    df["interval"] * 1048576
)
df.timestamp *= 1 / 3600.0

df.drop(df[df.node_id.str.contains("slices")].index, inplace=True)

if MATCH:
    df.drop(df[~df.node_id.str.contains(MATCH)].index, inplace=True)
    df.replace({"node_id": {MATCH: ""}}, inplace=True, regex=True)

metrics = [
    ("proc_cpu_usage", "Process CPU usage"),
    ("load_avg_1", "Load average (1 minute)"),
    ("mem_occupancy", "Memory occupancy"),
    ("tot_throughput", "Network traffic per node (Mb/s)"),
    ("active_power", "Active power (mW)"),
]

if BOX:
    for y, ylabel in metrics:
        fig, ax = plt.subplots()
        sns.boxplot(df, x="node_id", y=y, ax=ax)
        ax.set_ylabel(ylabel)
        show_or_save("{}-{}-box".format(basename, y))

if TIME:
    for y, ylabel in metrics:
        fig, ax = plt.subplots()
        sns.lineplot(df, x="timestamp", y=y, hue="node_id", ax=ax)
        ax.set_xlabel("Time (h)")
        ax.set_ylabel(ylabel)
        fig.suptitle("")
        show_or_save("{}-{}-time".format(basename, y))

if SHOW:
    input("Press any key to continue")
