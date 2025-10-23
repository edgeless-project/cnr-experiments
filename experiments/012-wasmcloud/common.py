#!/usr/bin/env python3

import os
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import seaborn as sns

IMAGE_TYPE = os.environ.get("IMAGE_TYPE", "pdf")


def load_node_names(capabilities: str):
    df = pd.read_csv(capabilities)
    ret = dict()
    for _id, node_id, labels in df[["node_id", "labels"]].itertuples():
        labels = str(labels).replace("[", "").replace("]", "").split(";")
        hostname = node_id
        for label in labels:
            if "hostname=" in label:
                (_token, hostname) = label.split("=")
        ret[node_id] = hostname
    return ret


def map_physical_to_workflow_id(input_file: str):
    df = pd.read_csv(input_file)
    ret = dict()
    for _id, workflow_id, physical_id in df[
        ["workflow_id", "physical_id"]
    ].itertuples():
        ret[physical_id] = workflow_id
    return ret


def plot_node_health(df: pd.DataFrame, experiment_label: str, time_ranges: list):
    # add experiment labels
    df["experiment"] = ""
    for i, row in df.iterrows():
        for time_range in time_ranges:
            (begin, end, experiment) = time_range
            begin = float(begin)
            end = float(end)
            if row["timestamp"] >= begin and row["timestamp"] <= end:
                df.at[i, "experiment"] = experiment
                break
    df.replace(
        {
            "experiment": {
                "": np.nan,
            }
        },
        inplace=True,
    )
    df.dropna(subset=["experiment"], inplace=True)

    df["mem_occupancy"] = (df["mem_used"] / df["mem_available"]) * 100

    df["rx_throughput"] = df.groupby(["seed", "node_id"])["tot_rx_bytes"].diff()
    df["tx_throughput"] = df.groupby(["seed", "node_id"])["tot_rx_bytes"].diff()
    df["interval"] = df.groupby(["seed", "node_id"])["timestamp"].diff()
    df["tot_throughput"] = (df["rx_throughput"] + df["tx_throughput"]) / (
        df["interval"] * 1048576
    )
    # df.timestamp *= 1 / 3600.0

    # select only some nodes
    match = "rpi-"
    df.drop(df[~df.node_id.str.contains(match)].index, inplace=True)
    df.replace({"node_id": {match: ""}}, inplace=True, regex=True)

    for experiment in df["experiment"].unique():
        df.loc[df["experiment"] == experiment, "timestamp"] = (
            df.loc[df["experiment"] == experiment, "timestamp"]
            - df[df["experiment"] == experiment]["timestamp"].min()
        )

    bin_duration = 10
    df["timestamp_bin"] = (df["timestamp"] / bin_duration).apply(np.floor)

    metrics = [
        ("load_avg_1", "Average load"),
        ("mem_occupancy", "Memory occupancy"),
        ("tot_throughput", "Network traffic per node (Mb/s)"),
    ]

    basename = os.path.basename(os.getcwd())
    for y, ylabel in metrics:
        fig, ax = plt.subplots()
        sns.lineplot(
            df,
            x="timestamp_bin",
            y=y,
            hue="experiment",
            errorbar=("ci", 95),
            ax=ax,
            estimator="mean",
        )
        ax.set_xlabel("Time (s)")
        # ax.set_xlim(left=0.0, right=60.0)
        ax.set_ylabel(ylabel)
        fig.suptitle("")
        plt.savefig("{}-{}-{}.{}".format(basename, y, experiment_label, IMAGE_TYPE))


def plot_latencies(df: pd.DataFrame, experiment_label: str):
    for size in df["size"].unique():
        df.loc[df["size"] == size, "timestamp"] = (
            df.loc[df["size"] == size, "timestamp"]
            - df[df["size"] == size]["timestamp"].min()
        )

    df["latency"] *= 1000.0

    bin_duration = 10
    df["timestamp_bin"] = (df["timestamp"] / bin_duration).apply(np.floor)

    metrics = [
        ("latency", "Application latency (ms)"),
    ]

    basename = os.path.basename(os.getcwd())
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
        ax.set_xlabel("Time (s)")
        ax.set_ylabel(ylabel)
        ax.set_xlim(left=0.0, right=60.0)
        fig.suptitle("")
        plt.savefig("{}-{}-{}.{}".format(basename, y, experiment_label, IMAGE_TYPE))

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
    ax.set_xlim(left=0.0, right=60.0)
    fig.suptitle("")
    plt.savefig("{}-throughput-{}.{}".format(basename, experiment_label, IMAGE_TYPE))
