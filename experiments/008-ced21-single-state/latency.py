#!/usr/bin/env python3

import pandas as pd
import os
import random
import matplotlib.pyplot as plt
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


basename = os.path.basename(os.getcwd())

workflows = {}
with open(WORKFLOWS_CSV, "r") as infile:
    for line in infile:
        (wf_id, experiment, size) = line.rstrip().split(",")
        workflows[wf_id] = [experiment, size]

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

        assert wid in workflows
        experiment = "-".join(workflows[wid])

        if tbegin is not None and tend is not None:
            latencies.append([wid, tbegin, tend - tbegin, experiment])
            delivered += 1
        else:
            lost += 1
    if (delivered + lost) > 0:
        losses.append([wid, float(lost) / (delivered + lost)])

print(losses)

df = pd.DataFrame(latencies, columns=["wid", "timestamp", "latency", "experiment"])
df["timestamp_bin"] = (df["timestamp"] / 60).apply(np.floor)

metrics = [
    ("latency", "Latency (s)"),
]

basename = os.path.basename(os.getcwd())
for y, ylabel in metrics:
    fig, ax = plt.subplots()
    sns.boxplot(df, x="experiment", y=y, ax=ax)
    ax.set_ylabel(ylabel)
    show_or_save("{}-{}".format(basename, y))

if SHOW:
    input("Press any key to continue")
