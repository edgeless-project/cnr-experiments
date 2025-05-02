#!/usr/bin/env python3

import pandas as pd
import os
import matplotlib.pyplot as plt
import seaborn as sns
from utils import box_plot, time_plot, load_dataset

HEALTH_STATUS = os.environ.get("HEALTH_STATUS", "dataset/health_status.csv")
SHOW = bool(os.environ.get("SHOW", ""))

basename = os.path.basename(os.getcwd())

df = load_dataset(HEALTH_STATUS, min_timestamp=0, max_timestamp=7200)

df["mem_occupancy"] = (df["mem_used"] / df["mem_available"]) * 100

df["rx_throughput"] = df.groupby(["seed", "node_id"])["tot_rx_bytes"].diff()
df["tx_throughput"] = df.groupby(["seed", "node_id"])["tot_rx_bytes"].diff()
df["interval"] = df.groupby(["seed", "node_id"])["timestamp"].diff()
df["tot_throughput"] = (df["rx_throughput"] + df["tx_throughput"]) / (
    df["interval"] * 1048576
)

metrics = [
    ("proc_cpu_usage", "Process CPU usage"),
    ("load_avg_1", "Load average (1 minute)"),
    ("mem_occupancy", "Memory occupancy"),
    ("tot_throughput", "Network traffic per node (Mb/s)"),
]

for y, ylabel in metrics:
    box_plot(
        df,
        x="node_id",
        y=y,
        ylabel=ylabel,
        ylim=None,
        yscale="linear",
        hue=None,
        show=SHOW,
        filename="{}-{}-box".format(basename, y),
    )

for y, ylabel in metrics:
    time_plot(
        df,
        x="timestamp",
        y=y,
        ylabel=ylabel,
        hue="node_id",
        show=SHOW,
        filename="{}-{}-time".format(basename, y),
    )

if SHOW:
    input("Press any key to continue")
