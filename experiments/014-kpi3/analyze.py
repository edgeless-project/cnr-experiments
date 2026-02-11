#!/usr/bin/env python3

import os
import os.path
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

IMAGE_TYPE = os.environ.get("IMAGE_TYPE", "pdf")

basename = os.path.basename(os.getcwd())

df_viewer_list = []
df_health_list = []
df_samples_list = []

node_id_to_hostnames = dict()
pid_to_wid = dict()
for experiment in os.listdir("data"):

    # Read the output of the viewer file.
    filename = f"data/{experiment}/data/viewer.dat"
    if not os.path.isfile(filename):
        continue
    df = pd.read_csv(filename, header=None, names=["timestamp"])
    df["experiment"] = experiment
    df_viewer_list.append(df)

    for orc in os.listdir(f"data/{experiment}"):
        dirname = f"data/{experiment}/{orc}"
        if not os.path.isdir(dirname) or not os.path.isfile(
            f"{dirname}/capabilities.csv"
        ):
            continue

        # Find from the capabilities the mapping:
        # - node_id -> hostname
        df = pd.read_csv(f"{dirname}/capabilities.csv")
        for _id, node_id, labels in df[["node_id", "labels"]].itertuples():
            labels = str(labels).replace("[", "").replace("]", "").split(";")
            hostname = node_id
            for label in labels:
                if "hostname=" in label:
                    (_token, hostname) = label.split("=")
            node_id_to_hostnames[node_id] = hostname

        # Find from the mapping_to_instance_id the mapping:
        # - node_id -> hostname
        df = pd.read_csv(f"{dirname}/mapping_to_instance_id.csv")
        for _id, workflow_id, physical_id in df[
            ["workflow_id", "physical_id"]
        ].itertuples():
            pid_to_wid[physical_id] = workflow_id

        # Read the node health dataset.
        df = pd.read_csv(f"{dirname}/health_status.csv")
        df["experiment"] = experiment
        df_health_list.append(df)

        df["mem_occupancy"] = (df["mem_used"] / df["mem_available"]) * 100

        # Read the performance samples dataset.
        df = pd.read_csv(f"{dirname}/performance_samples.csv")
        df["experiment"] = experiment
        df_samples_list.append(df)

df_viewer = pd.concat(df_viewer_list, ignore_index=True)
df_health = pd.concat(df_health_list, ignore_index=True)
df_samples = pd.concat(df_samples_list, ignore_index=True)

df_health["hostname"] = df_health["node_id"].map(node_id_to_hostnames)
df_health["node_type"] = df_health["hostname"].str.extract(r"^([^-]+)")

df_samples["workflow_id"] = df_samples["identifier"].map(pid_to_wid)

# Aggregates in new data frames

df_viewer_tpt = (
    df_viewer.groupby("experiment")["timestamp"]
    .agg(lambda x: x.count() / (x.max() - x.min()))
    .reset_index(name="throughput")
)

df_throughput = (
    df_health.groupby(["experiment", "node_id"])
    .apply(
        lambda x: (
            x["tot_rx_bytes"].max()
            - x["tot_rx_bytes"].min()
            + x["tot_tx_bytes"].max()
            - x["tot_tx_bytes"].min()
        )
        / (x["timestamp"].max() - x["timestamp"].min())
    )
    .mul(0.001)
    .reset_index(name="throughput")
)

df_samples_latency = (
    df_samples.groupby(["experiment", "workflow_id", "identifier"])["value"]
    .mean()
    .groupby(["experiment", "workflow_id"])
    .sum()
    .mul(1000.0)
    .reset_index(name="latency")
)

if not os.path.isdir("plots"):
    os.mkdir("plots")

# Application throughput
fig, ax = plt.subplots()
sns.barplot(df_viewer_tpt, x="experiment", y="throughput", ax=ax, legend=False)
ax.set_xlabel("Experiment")
ax.set_ylabel("Application throughput (messages/s)")
fig.suptitle("")
plt.savefig(f"plots/{basename}-app-throughput.{IMAGE_TYPE}")

# Network traffic
fig, ax = plt.subplots()
sns.boxplot(df_throughput, x="experiment", y="throughput", ax=ax, legend=False)
ax.set_xlabel("Experiment")
ax.set_ylabel("Average node traffic (kb/s)")
fig.suptitle("")
plt.savefig(f"plots/{basename}-network-throughput.{IMAGE_TYPE}")

# Health metrics
metrics = [
    ("proc_cpu_usage", "Average CPU utilization"),
    ("gpu_load_perc", "Average GPU utilization"),
    ("mem_occupancy", "Memory occupancy (%)"),
    ("active_power", "Active power (mW)"),
]

for metric, label in metrics:
    fig, ax = plt.subplots()
    if metric == "gpu_load_perc":
        sns.violinplot(df_health, x="experiment", y=metric, ax=ax, legend=False)
    else:
        sns.violinplot(
            df_health, x="experiment", y=metric, hue="node_type", ax=ax, legend=True
        )
    ax.set_xlabel("Experiment")
    ax.set_ylabel(label)
    fig.suptitle("")
    plt.savefig(f"plots/{basename}-{metric}.{IMAGE_TYPE}")

# Workflow metrics
fig, ax = plt.subplots()
sns.violinplot(df_samples_latency, x="experiment", y="latency", ax=ax, legend=False)
ax.set_xlabel("Experiment")
ax.set_ylabel("Workflow latency (ms)")
fig.suptitle("")
plt.savefig(f"plots/{basename}-network-throughput.{IMAGE_TYPE}")
