#!/usr/bin/env python3

import pandas as pd
import os
import matplotlib.pyplot as plt
import seaborn as sns
from utils import box_plot, load_dataset, map_physical_to_node_id, load_node_names

PERFORMANCE_SAMPLES = os.environ.get(
    "PERFORMANCE_SAMPLES", "dataset/performance_samples.csv"
)
SHOW = bool(os.environ.get("SHOW", ""))
IMAGE_TYPE = os.environ.get("IMAGE_TYPE", "pdf")
MIN_TIMESTAMP = float(os.environ.get("MIN_TIMESTAMP", "0"))
MAX_TIMESTAMP = float(os.environ.get("MAX_TIMESTAMP", "650"))

basename = os.path.basename(os.getcwd())

df = load_dataset(
    PERFORMANCE_SAMPLES, min_timestamp=MIN_TIMESTAMP, max_timestamp=MAX_TIMESTAMP
)

df = df[df["metric"].isin(["function_execution_time", "function_transfer_time"])]

df.replace(map_physical_to_node_id(), inplace=True)
df.rename(columns={"identifier": "node_id"}, inplace=True)
df.replace(load_node_names(), inplace=True)

match = "orin-"
df.drop(df[~df.node_id.str.contains(match)].index, inplace=True)
df.replace({"node_id": {match: ""}}, inplace=True, regex=True)

metrics = [
    ("function_execution_time", "Function execution time (ms)"),
    ("function_transfer_time", "Function transfer time (ms)"),
]

df.value *= 1000.0
for y, ylabel in metrics:
    fig, ax = plt.subplots()
    sns.lineplot(df[df["metric"] == y], x="timestamp", y="value", ax=ax, legend=False)
    ax.set_ylabel(ylabel)
    ax.set_ylim((1, 100))
    ax.set_yscale("log")
    fig.suptitle("")
    if SHOW:
        plt.show(block=False)
    else:
        plt.savefig("{}.{}".format("{}-{}".format(basename, y), IMAGE_TYPE))


if SHOW:
    input("Press any key to continue")
