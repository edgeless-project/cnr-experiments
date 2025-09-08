#!/usr/bin/env python3

import pandas as pd
import os
import matplotlib.pyplot as plt
import seaborn as sns

IMAGE_TYPE = os.environ.get("IMAGE_TYPE", "pdf")
SHOW = bool(os.environ.get("SHOW", ""))


def show_or_save(filename: str):
    if SHOW:
        plt.show(block=False)
    else:
        plt.savefig("{}.{}".format(filename, IMAGE_TYPE))


def load_dataset(
    filename: str,
    capabilities: str,
    min_timestamp: float | None,
    max_timestamp: float | None,
):
    pd_set_options()

    df = pd.read_csv(filename)

    df["timestamp"] = df["timestamp"] - df["timestamp"].min()
    if min_timestamp:
        df.drop(df[df.timestamp < min_timestamp].index, inplace=True)
    if max_timestamp:
        df.drop(df[df.timestamp > max_timestamp].index, inplace=True)

    df.replace(load_node_names(capabilities), inplace=True)

    return df


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


def pd_set_options():
    pd.set_option("display.show_dimensions", False)
    pd.set_option("display.max_columns", None)
    pd.set_option("display.max_colwidth", None)


def map_physical_to_workflow_id(input_file: str):
    df = pd.read_csv(input_file)
    ret = dict()
    for _id, workflow_id, physical_id in df[
        ["workflow_id", "physical_id"]
    ].itertuples():
        ret[physical_id] = workflow_id
    return ret
