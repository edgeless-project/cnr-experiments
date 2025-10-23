#!/usr/bin/env python3

import pandas as pd
import os
from sys import float_info
from common import plot_latencies, map_physical_to_workflow_id

MAPPING_TO_INSTANCE_ID = os.environ.get(
    "MAPPING_TO_INSTANCE_ID", "data/edgeless/dataset/mapping_to_instance_id.csv"
)
WORKFLOWS_CSV = os.environ.get("WORKFLOWS_CSV", "data/edgeless/workflows.csv")
PERFORMANCE_SAMPLES = os.environ.get(
    "PERFORMANCE_SAMPLES", "data/edgeless/dataset/performance_samples.csv"
)


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

plot_latencies(df, "edgeless")
