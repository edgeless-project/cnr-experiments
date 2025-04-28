#!/usr/bin/env python3

import pandas as pd
import os
import matplotlib.pyplot as plt
import seaborn as sns

IMAGE_TYPE = os.environ.get("IMAGE_TYPE", "pdf")
HEALTH_STATUS = os.environ.get("HEALTH_STATUS", "dataset/health_status.csv")
CAPABILITIES = os.environ.get("CAPABILITIES", "dataset/capabilities.csv")
SHOW = bool(os.environ.get("SHOW", ""))


def plot(df, x: str, y: str, hue: str | None, ylabel: str, show: bool, filename: str):
    fig, ax = plt.subplots()
    sns.boxplot(df, x=x, y=y, hue=hue, ax=ax)
    ax.set_ylabel(ylabel)
    ax.set_title("")
    fig.suptitle("")
    if show:
        plt.show(block=False)
    else:
        plt.savefig("{}.{}".format(filename, IMAGE_TYPE))


def time_plot(
    df, x: str, y: str, hue: str | None, ylabel: str, show: bool, filename: str
):
    fig, ax = plt.subplots()
    sns.lineplot(df, x=x, y=y, hue=hue, ax=ax)
    ax.set_ylabel(ylabel)
    ax.set_title("")
    fig.suptitle("")
    if show:
        plt.show(block=False)
    else:
        plt.savefig("{}.{}".format(filename, IMAGE_TYPE))


def pd_set_options():
    pd.set_option("display.show_dimensions", False)
    pd.set_option("display.max_columns", None)
    pd.set_option("display.max_colwidth", None)


def load_node_names():
    df = pd.read_csv(CAPABILITIES)
    ret = dict()
    for _id, node_id, labels in df[["node_id", "labels"]].itertuples():
        labels = str(labels).replace("[", "").replace("]", "")
        ret[node_id] = labels
    return ret


pd_set_options()
node_names = load_node_names()
basename = os.path.basename(os.getcwd())

df = pd.read_csv(HEALTH_STATUS)
df["timestamp"] = df["timestamp"] - df["timestamp"].min()
df.drop(df[df.timestamp > 86400].index, inplace=True)

df = df.replace(node_names)

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
    plot(
        df,
        x="node_id",
        y=y,
        ylabel=ylabel,
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
