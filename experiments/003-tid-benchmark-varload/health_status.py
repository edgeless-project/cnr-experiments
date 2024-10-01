#!/usr/bin/env python3

import os
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

IMAGE_TYPE = os.environ.get("IMAGE_TYPE", "png")
DATASET = os.environ.get("DATASET", "dataset/health_status.csv")
CAPABILITIES = os.environ.get("DATASET", "dataset/capabilities.csv")
SHOW = bool(os.environ.get("SHOW", ""))
WARMUP = float(os.environ.get("WARMUP", "0.1"))


def plot(
    df,
    x: str,
    y: str,
    ylim: list,
    ylabel: str | None,
    hue: str | None,
    hue_order: list | None,
    title: str | None,
    show: bool,
    filename: str,
):
    fig, ax = plt.subplots()
    sns.boxplot(df, x=x, y=y, hue=hue, ax=ax, hue_order=hue_order)
    ax.set_title(title)
    ax.set_ylim(ylim)
    ax.set_ylabel(ylabel)
    fig.suptitle("")
    if show:
        plt.show(block=False)
    else:
        plt.savefig("{}.{}".format(filename, IMAGE_TYPE))


assert 0 <= WARMUP <= 1

df = pd.read_csv(DATASET)
min_ts, max_ts = df["timestamp"].min(), df["timestamp"].max()
warmup_ts = min_ts + (max_ts - min_ts) * WARMUP
df = df[df["timestamp"] >= warmup_ts]

caps = pd.read_csv(CAPABILITIES)
caps = caps[caps["runtimes"] != "[]"]
node_ids = caps["node_id"].unique()

df = df[df["node_id"].isin(node_ids)]

node_id_names = {}
for i, j in zip(sorted(node_ids), range(len(node_ids))):
    node_id_names[i] = "node#{}".format(j)
df = df.replace(node_id_names)

basename = os.path.basename(os.getcwd())

metrics = [
    ("load_avg_1", "Node load"),
    ("proc_cpu_usage", "CPU usage (%)"),
    ("proc_memory", "Process memory (B)"),
    ("proc_vmemory", "Process vmemory (B)"),
]

for ymetric, ylabel in metrics:
    ylim = [df[ymetric].min(), df[ymetric].max()]
    for orchestration in df["orchestration"].unique():
        plot(
            df[df["orchestration"] == orchestration],
            x="interarrival",
            y=ymetric,
            ylim=ylim,
            ylabel=ylabel,
            hue="node_id",
            hue_order=sorted(node_id_names.values()),
            title=orchestration,
            show=SHOW,
            filename="{}-{}-{}".format(basename, orchestration, ymetric),
        )

df_grouped = df.groupby(["seed", "interarrival", "node_id", "orchestration"])
df_new = (
    (
        df_grouped["tot_rx_bytes"].max()
        - df_grouped["tot_rx_bytes"].min()
        + df_grouped["tot_tx_bytes"].max()
        - df_grouped["tot_tx_bytes"].min()
    )
    * (1e-6)
).to_frame()
df_new.columns = ["value"]

plot(
    df_new,
    x="interarrival",
    y="value",
    ylim=None,
    ylabel="Total traffic per node (MB)",
    hue="orchestration",
    hue_order=None,
    title=None,
    show=SHOW,
    filename="{}-traffic".format(basename),
)

if SHOW:
    input("Press any key to continue")
