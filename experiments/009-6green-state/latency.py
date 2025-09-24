#!/usr/bin/env python3

import pandas as pd
import os
import random
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import seaborn as sns
import numpy as np
from utils import show_or_save, map_physical_to_workflow_id
from sys import float_info

MAPPING_TO_INSTANCE_ID = os.environ.get(
    "MAPPING_TO_INSTANCE_ID", "data/dataset/mapping_to_instance_id.csv"
)
WORKFLOWS_CSV = os.environ.get("WORKFLOWS_CSV", "workflows.csv")
PERFORMANCE_SAMPLES = os.environ.get(
    "PERFORMANCE_SAMPLES", "data/dataset/performance_samples.csv"
)
TIMESTAMP_END = float(os.environ.get("TIMESTAMP_END", "-1"))
SHOW = bool(os.environ.get("SHOW", ""))


def relabel(df):
    df.replace(
        {
            "experiment": {
                "local": "L",
                "remote": "R",
            }
        },
        inplace=True,
    )
    df.replace(
        {
            "size": {
                "1000": "1k",
                "100000": "100k",
            }
        },
        inplace=True,
    )
    df["label"] = df["experiment"] + "-" + df["size"]


basename = os.path.basename(os.getcwd())

workflows = {}
with open(WORKFLOWS_CSV, "r") as infile:
    for line in infile:
        (wf_id, experiment, size, num) = line.rstrip().split(",")
        workflows[wf_id] = [experiment, size, int(num)]

pid_to_wid = map_physical_to_workflow_id(MAPPING_TO_INSTANCE_ID)
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

        if wid not in workflows:
            continue

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
time_range = {}
for wid, timestamps in timestamps.items():
    delivered = 0
    lost = 0

    assert wid in workflows
    experiment = workflows[wid][0]
    size = workflows[wid][1]
    num_workflows = workflows[wid][2]

    for _msg_id, ids in timestamps.items():
        tbegin = ids[0] - min_timestamp if ids[0] is not None else None
        tend = ids[1] - min_timestamp if ids[1] is not None else None

        if TIMESTAMP_END >= 0 and (
            (tbegin is not None and tbegin > TIMESTAMP_END)
            or (tend is not None and tend > TIMESTAMP_END)
        ):
            continue

        if tbegin is not None and tend is not None:
            label = f"{experiment},{size},{num_workflows}"
            if label not in time_range:
                time_range[label] = [tbegin, tend]
            else:
                time_range[label][0] = min(time_range[label][0], tbegin)
                time_range[label][1] = max(time_range[label][1], tend)

            latencies.append(
                [wid, tbegin, tend - tbegin, experiment, size, num_workflows]
            )
            delivered += 1
        else:
            lost += 1
    if (delivered + lost) > 0:
        losses.append(
            [wid, experiment, size, num_workflows, float(lost) / (delivered + lost)]
        )

with open("workflow-ranges.csv", "w") as outfile:
    for label, (begin, end) in time_range.items():
        outfile.write(f"{begin + min_timestamp},{end+min_timestamp},{label}\n")

losses_df = pd.DataFrame(
    losses,
    columns=["wid", "experiment", "size", "num_workflows", "loss"],
)
relabel(losses_df)
fig, ax = plt.subplots()
sns.barplot(losses_df, x="label", y="loss", hue="num_workflows", errorbar=None)
ax.set_ylabel("Loss ratio")
plt.xticks(rotation=45)
show_or_save("{}-loss".format(basename))

df = pd.DataFrame(
    latencies,
    columns=["wid", "timestamp", "latency", "experiment", "size", "num_workflows"],
)
relabel(df)

metrics = [
    ("latency", "Latency (ms)"),
]

basename = os.path.basename(os.getcwd())

df["latency"] = df["latency"].apply(lambda x: x * 1000)
for y, ylabel in metrics:
    fig, ax = plt.subplots()
    sns.boxplot(
        df,
        x="label",
        y=y,
        hue="num_workflows",
        ax=ax,
        showfliers=False,
    )
    ax.set_ylim(bottom=0.1, top=100)
    ax.set_ylabel(ylabel)
    ax.set_yscale("log")
    plt.xticks(rotation=45)
    ax.yaxis.set_major_formatter(
        ticker.FuncFormatter(
            lambda y, pos: (
                "{{:.{:1d}f}}".format(int(np.maximum(-np.log10(y), 0)))
            ).format(y)
        )
    )
    show_or_save("{}-{}".format(basename, y))

new_df = pd.DataFrame(
    df.groupby(["label", "num_workflows"], as_index=False).agg("count")
)
new_df["norm_tpt"] = new_df["wid"] / 120.0

fig, ax = plt.subplots()
sns.barplot(new_df, x="label", y="norm_tpt", hue="num_workflows")
ax.set_ylabel("Total throughput (messages/s)")
plt.xticks(rotation=45)
show_or_save("{}-throughput".format(basename))

if SHOW:
    input("Press any key to continue")
