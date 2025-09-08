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


basename = os.path.basename(os.getcwd())

workflows = {}
with open(WORKFLOWS_CSV, "r") as infile:
    for line in infile:
        (wf_id, experiment, size, num) = line.rstrip().split(",")
        workflows[wf_id] = [f"{experiment}-{size}", num]

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
        experiment = workflows[wid][0]
        num_workflows = workflows[wid][1]

        if tbegin is not None and tend is not None:
            latencies.append([wid, tbegin, tend - tbegin, experiment, num_workflows])
            delivered += 1
        else:
            lost += 1
    if (delivered + lost) > 0:
        losses.append([wid, float(lost) / (delivered + lost)])

for wf_id, loss in losses:
    print("{}, loss {}".format(wf_id, loss))

df = pd.DataFrame(
    latencies, columns=["wid", "timestamp", "latency", "experiment", "num_workflows"]
)
df["timestamp_bin"] = (df["timestamp"] / 60).apply(np.floor)

metrics = [
    ("latency", "Latency (ms)"),
]

basename = os.path.basename(os.getcwd())
replacements = {
    "local-1": "L-1",
    "local-100": "L-100",
    "local-100000": "L-100k",
    "remote-1": "R-1",
    "remote-100": "R-100",
    "remote-100000": "R-100k",
}
df.replace({"experiment": replacements}, inplace=True)
df["latency"] = df["latency"].apply(lambda x: x * 1000)
for num_workflow in df["num_workflows"].unique():
    for y, ylabel in metrics:
        fig, ax = plt.subplots()
        sns.boxplot(
            df[df["num_workflows"] == num_workflow],
            x="experiment",
            y=y,
            ax=ax,
            showfliers=False,
        )
        ax.set_ylim(bottom=0.1, top=100)
        ax.set_ylabel(ylabel)
        ax.set_yscale("log")
        ax.yaxis.set_major_formatter(
            ticker.FuncFormatter(
                lambda y, pos: (
                    "{{:.{:1d}f}}".format(int(np.maximum(-np.log10(y), 0)))
                ).format(y)
            )
        )
        plural = ""
        if int(num_workflow) > 1:
            plural = "s"
        fig.suptitle(f"{num_workflow} workflow{plural}")
        show_or_save("{}-{}-{}".format(basename, num_workflow, y))

if SHOW:
    input("Press any key to continue")
