#!/usr/bin/env python3

import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from utils import show_or_save, pd_set_options, load_node_names

DATA_DIR = os.environ.get("DATA_DIR", "data")
SHOW = bool(os.environ.get("SHOW", ""))

dfs = []
experiments = next(os.walk(DATA_DIR))[1]
for experiment in experiments:
    pd_set_options()

    df = pd.read_csv(
        f"{DATA_DIR}/{experiment}/dataset/health_status.csv",
    )
    df.replace(
        load_node_names(
            f"{DATA_DIR}/{experiment}/dataset/capabilities.csv",
        ),
        inplace=True,
    )

    df["mem_occupancy"] = (df["mem_used"] / df["mem_available"]) * 100

    df["rx_throughput"] = df.groupby(["seed", "node_id"])["tot_rx_bytes"].diff()
    df["tx_throughput"] = df.groupby(["seed", "node_id"])["tot_rx_bytes"].diff()
    df["interval"] = df.groupby(["seed", "node_id"])["timestamp"].diff()
    df["tot_throughput"] = (df["rx_throughput"] + df["tx_throughput"]) / (
        df["interval"] * 1048576
    )
    df.timestamp *= 1 / 3600.0

    df.drop(df[~df.node_id.str.contains("orin-")].index, inplace=True)
    df.replace({"node_id": {"orin-": ""}}, inplace=True, regex=True)

    dfs.append(df)

df = pd.concat(
    [d.assign(experiment=name) for d, name in zip(dfs, experiments)],
    ignore_index=True,
)

metrics = [
    ("proc_cpu_usage", "Process CPU usage"),
    ("tot_throughput", "Network traffic per node (Mb/s)"),
    ("active_power", "Active power (mW)"),
]

basename = os.path.basename(os.getcwd())
for y, ylabel in metrics:
    fig, ax = plt.subplots()
    sns.boxplot(df, x="experiment", y=y, ax=ax)
    ax.set_ylabel(ylabel)
    show_or_save("{}-{}".format(basename, y))

if SHOW:
    input("Press any key to continue")
