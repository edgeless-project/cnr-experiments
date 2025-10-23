#!/usr/bin/env python3

import pandas as pd
import os
import random
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import seaborn as sns
import numpy as np
from sys import float_info

MAPPING_TO_INSTANCE_ID = os.environ.get(
    "MAPPING_TO_INSTANCE_ID", "data/edgeless/dataset/mapping_to_instance_id.csv"
)
WORKFLOWS_CSV = os.environ.get("WORKFLOWS_CSV", "data/edgeless/workflows.csv")
PERFORMANCE_SAMPLES = os.environ.get(
    "PERFORMANCE_SAMPLES", "data/edgeless/dataset/performance_samples.csv"
)
IMAGE_TYPE = os.environ.get("IMAGE_TYPE", "pdf")
SHOW = bool(os.environ.get("SHOW", ""))


def map_physical_to_workflow_id(input_file: str):
    df = pd.read_csv(input_file)
    ret = dict()
    for _id, workflow_id, physical_id in df[
        ["workflow_id", "physical_id"]
    ].itertuples():
        ret[physical_id] = workflow_id
    return ret


basename = os.path.basename(os.getcwd())

workflows = {}
with open(WORKFLOWS_CSV, "r") as infile:
    for line in infile:
        (wf_id, size) = line.rstrip().split(",")
        workflows[wf_id] = size

pid_to_wid = map_physical_to_workflow_id(MAPPING_TO_INSTANCE_ID)
timestamps = {}
min_timestamp = float_info.max
with open(PERFORMANCE_SAMPLES, "r") as infile:
    for line in infile:
        if "tbegin" not in line and "tend" not in line:
            continue
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
for wid, timestamps in timestamps.items():
    delivered = 0
    lost = 0
    for _msg_id, ids in timestamps.items():
        tbegin = ids[0] - min_timestamp if ids[0] is not None else None
        tend = ids[1] - min_timestamp if ids[1] is not None else None

        assert wid in workflows

        if tbegin is not None and tend is not None:
            latencies.append([wid, tbegin, tend - tbegin, workflows[wid]])
            delivered += 1
        else:
            lost += 1
    if (delivered + lost) > 0:
        losses.append([wid, float(lost) / (delivered + lost)])

for wf_id, loss in losses:
    print("{}, loss {}".format(wf_id, loss))

df = pd.DataFrame(latencies, columns=["wid", "timestamp", "latency", "size"])

for size in df["size"].unique():
    df.loc[df["size"] == size, "timestamp"] = (
        df.loc[df["size"] == size, "timestamp"]
        - df[df["size"] == size]["timestamp"].min()
    )


bin_duration = 10
df["timestamp_bin"] = (df["timestamp"] / bin_duration).apply(np.floor)

metrics = [
    ("latency", "Latency (ms)"),
]

df["latency"] *= 1000.0

for y, ylabel in metrics:
    fig, ax = plt.subplots()
    sns.lineplot(
        df,
        x="timestamp_bin",
        y=y,
        hue="size",
        errorbar=("ci", 95),
        ax=ax,
        estimator="mean",
    )
    ax.set_ylabel(ylabel)
    # ax.set_xlim(left=0.0, right=60.0)
    # ax.set_yscale("log")
    fig.suptitle("")
    plt.savefig("{}-{}-edgeless.{}".format(basename, y, IMAGE_TYPE))

grouped = df.groupby(["timestamp_bin", "size"])["latency"].count().to_frame()
grouped["latency"] /= bin_duration

fig, ax = plt.subplots()
sns.lineplot(
    grouped,
    x="timestamp_bin",
    y="latency",
    hue="size",
    errorbar=("ci", 95),
    ax=ax,
    estimator="count",
)
ax.set_xlabel("Time (s)")
ax.set_ylabel("Throughput (messages/s)")
# ax.set_xlim(left=0.0, right=60.0)
fig.suptitle("")
plt.savefig("{}-throughput-edgeless.{}".format(basename, IMAGE_TYPE))
