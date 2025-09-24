#!/usr/bin/env python3

import pandas as pd
import os
import random
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from utils import (
    time_plot,
    ecdf_plot,
    map_physical_to_workflow_id,
    show_or_save,
)
from sys import float_info

MAX_WORKFLOWS = 10
PERFORMANCE_SAMPLES = os.environ.get(
    "PERFORMANCE_SAMPLES", "dataset/performance_samples.csv"
)
TIMESTAMP_END = float(os.environ.get("TIMESTAMP_END", "-1"))
SHOW = bool(os.environ.get("SHOW", ""))
IMAGE_TYPE = os.environ.get("IMAGE_TYPE", "pdf")

basename = os.path.basename(os.getcwd())

pid_to_wid = map_physical_to_workflow_id()
timestamps = {}
min_timestamp = float_info.max
with open(PERFORMANCE_SAMPLES, "r") as infile:
    for line in infile:
        (seed, identifier, metric, timestamp, value) = line.rstrip().split(",")
        if metric != "tbegin" and metric != "tend":
            continue
        timestamp = float(timestamp)
        min_timestamp = min(timestamp, min_timestamp)
        msg_id = int(value)
        if identifier not in pid_to_wid:
            print(
                "ignoring sample from unknown physical identifier {}".format(identifier)
            )
            continue
        wid = pid_to_wid[identifier]

        if wid not in timestamps:
            timestamps[wid] = {}
        if msg_id not in timestamps[wid]:
            timestamps[wid][msg_id] = [None, None]

        if metric == "tbegin":
            if timestamps[wid][msg_id][0] is None:
                timestamps[wid][msg_id][0] = timestamp
            else:
                print(
                    "dup timestamp of tbegin at {} for msg_id {} wid {}".format(
                        timestamp, msg_id, wid
                    )
                )
        elif metric == "tend":
            if timestamps[wid][msg_id][1] is None:
                timestamps[wid][msg_id][1] = timestamp
            else:
                print(
                    "dup timestamp of tend at {} for msg_id {} wid {}".format(
                        timestamp, msg_id, wid
                    )
                )

latencies = []
losses = []
for wid, timestamps in timestamps.items():
    delivered = 0
    lost = 0
    for _msg_id, ids in timestamps.items():
        tbegin = ids[0] - min_timestamp if ids[0] is not None else None
        tend = ids[1] - min_timestamp if ids[1] is not None else None

        if TIMESTAMP_END >= 0 and (
            (tbegin is not None and tbegin > TIMESTAMP_END)
            or (tend is not None and tend > TIMESTAMP_END)
        ):
            continue

        if tbegin is not None and tend is not None:
            latencies.append([wid, tbegin, tend - tbegin])
            delivered += 1
        else:
            lost += 1
    if (delivered + lost) > 0:
        losses.append([wid, float(lost) / (delivered + lost)])

for wid, loss_ratio in losses:
    print("{}: {}".format(wid, loss_ratio))
df_losses = pd.DataFrame(losses, columns=["wid", "loss"])

ecdf_plot(
    df_losses,
    x="loss",
    hue=None,
    show=SHOW,
    filename="{}-loss-ratio".format(basename),
)

df_latencies = pd.DataFrame(latencies, columns=["wid", "timestamp", "latency"])
df_latencies.latency *= 1000.0
# df_latencies["timestamp_bin"] = (df_latencies["timestamp"] / 60).apply(np.floor)
df_latencies["timestamp_bin"] = df_latencies["timestamp"].apply(np.floor)

df_throughput = pd.DataFrame(
    df_latencies.groupby("wid")["timestamp_bin"].value_counts()
)
fig, ax = plt.subplots()
sns.lineplot(
    df_throughput, x="timestamp_bin", y="count", hue="wid", ax=ax, legend=False
)
ax.set_xlabel("Time (s)")
ax.set_ylabel("Throughput (successful transactions/s)")
ax.set_title("")
fig.suptitle("")
show_or_save("{}-workflow-throghput".format(basename))

wids = list(df_latencies["wid"].unique())
selected = random.sample(wids, k=min(len(wids), MAX_WORKFLOWS))

df_latencies = df_latencies[df_latencies["wid"].isin(selected)]

# bottom = df_latencies["latency"].quantile(0.01)
# top = df_latencies["latency"].quantile(0.99)
bottom = 1
top = 1000

fig, ax = plt.subplots()
sns.lineplot(df_latencies, x="timestamp", y="latency", hue="wid", ax=ax, legend=False)
ax.set_ylabel("Latency (ms)")
ax.set_ylim((bottom, top))
ax.set_yscale("log")
fig.suptitle("")
if SHOW:
    plt.show(block=False)
else:
    plt.savefig("{}.{}".format("{}-workflow-latencies".format(basename), IMAGE_TYPE))

# for wid in wids:
#     time_plot(
#         df_latencies.loc[df_latencies["wid"] == wid],
#         x="timestamp",
#         y="latency",
#         ylabel="Latency (s)",
#         ylim=(bottom, top),
#         title=wid,
#         hue="wid",
#         show=SHOW,
#         filename="{}-workflow-{}-latency".format(basename, wid),
#     )


if SHOW:
    input("Press any key to continue")
