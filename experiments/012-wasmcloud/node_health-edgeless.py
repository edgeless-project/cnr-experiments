#!/usr/bin/env python3

import os
import pandas as pd
import numpy as np
from common import plot_node_health, load_node_names, map_physical_to_workflow_id

HEALTH_STATUS = os.environ.get(
    "HEALTH_STATUS", "data/edgeless/dataset/health_status.csv"
)
CAPABILITIES = os.environ.get("CAPABILITIES", "data/edgeless/dataset/capabilities.csv")
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
timestamps = []
with open(PERFORMANCE_SAMPLES, "r") as infile:
    for line in infile:
        if "tbegin" not in line and "tend" not in line:
            continue
        (seed, pid, metric, timestamp, value) = line.rstrip().split(",")
        if metric != "tbegin" and metric != "tend":
            continue
        timestamp = float(timestamp)
        if pid not in pid_to_wid:
            print("ignoring sample from unknown PID {}".format(pid))
            continue
        wid = pid_to_wid[pid]

        if wid not in workflows:
            continue

        size = workflows[wid]
        timestamps.append([size, timestamp])

df = pd.DataFrame(timestamps, columns=["size", "timestamp"])

time_ranges = []
for size in df["size"].unique():
    time_ranges.append(
        (
            df[df["size"] == size].min().timestamp,
            df[df["size"] == size].max().timestamp,
            size,
        )
    )
print(time_ranges)

df = pd.read_csv(HEALTH_STATUS)

df.replace(load_node_names(CAPABILITIES), inplace=True)

plot_node_health(df, "edgeless", time_ranges)
