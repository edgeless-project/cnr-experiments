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

basename = os.path.basename(os.getcwd())

df = load_dataset(PERFORMANCE_SAMPLES, min_timestamp=0, max_timestamp=7200)

df = df[df["metric"].isin(["function_execution_time", "function_transfer_time"])]

df.replace(map_physical_to_node_id(), inplace=True)
df.rename(columns={"identifier": "node_id"}, inplace=True)
df.replace(load_node_names(), inplace=True)


box_plot(
    df,
    x="node_id",
    y="value",
    ylabel="Latency (s)",
    ylim=[0, 0.1],
    yscale="linear",
    hue="metric",
    show=SHOW,
    filename="{}-latencies-box".format(basename),
)


if SHOW:
    input("Press any key to continue")
