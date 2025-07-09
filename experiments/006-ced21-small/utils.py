#!/usr/bin/env python3

import pandas as pd
import os
import matplotlib.pyplot as plt
import seaborn as sns

IMAGE_TYPE = os.environ.get("IMAGE_TYPE", "pdf")
CAPABILITIES = os.environ.get("CAPABILITIES", "dataset/capabilities.csv")
MAPPING_TO_INSTANCE_ID = os.environ.get(
    "MAPPING_TO_INSTANCE_ID", "dataset/mapping_to_instance_id.csv"
)
SHOW = bool(os.environ.get("SHOW", ""))


def show_or_save(filename: str):
    if SHOW:
        plt.show(block=False)
    else:
        plt.savefig("{}.{}".format(filename, IMAGE_TYPE))


def load_dataset(
    filename: str, min_timestamp: float | None, max_timestamp: float | None
):
    pd_set_options()

    df = pd.read_csv(filename)

    df["timestamp"] = df["timestamp"] - df["timestamp"].min()
    if min_timestamp:
        df.drop(df[df.timestamp < min_timestamp].index, inplace=True)
    if max_timestamp:
        df.drop(df[df.timestamp > max_timestamp].index, inplace=True)

    df.replace(load_node_names(), inplace=True)

    return df


def box_plot(
    df,
    x: str,
    y: str,
    hue: str | None,
    ylabel: str,
    ylim: tuple[float, float] | None,
    yscale: str,
    show: bool,
    filename: str,
):
    fig, ax = plt.subplots()
    sns.boxplot(df, x=x, y=y, hue=hue, ax=ax)
    ax.set_ylabel(ylabel)
    ax.set_ylim(ylim)
    ax.set_yscale(yscale)
    ax.set_title("")
    fig.suptitle("")
    if show:
        plt.show(block=False)
    else:
        plt.savefig("{}.{}".format(filename, IMAGE_TYPE))


def ecdf_plot(
    df,
    x: str,
    hue: str | None,
    show: bool,
    filename: str,
):
    fig, ax = plt.subplots()
    sns.ecdfplot(df, x=x, hue=hue, ax=ax)
    ax.set_ylabel("ECDF")
    ax.set_title("")
    fig.suptitle("")
    if show:
        plt.show(block=False)
    else:
        plt.savefig("{}.{}".format(filename, IMAGE_TYPE))


def time_plot(
    df,
    x: str,
    y: str,
    hue: str | None,
    ylabel: str,
    ylim: tuple[float, float] | None,
    title: str | None,
    show: bool,
    filename: str,
):
    fig, ax = plt.subplots()
    sns.lineplot(df, x=x, y=y, hue=hue, ax=ax)
    ax.set_ylabel(ylabel)
    if ylim is not None:
        ax.set_ylim(ylim)
    if title is not None:
        ax.set_title(title)
    fig.suptitle("")
    if show:
        plt.show(block=False)
    else:
        plt.savefig("{}.{}".format(filename, IMAGE_TYPE))


def pd_set_options():
    pd.set_option("display.show_dimensions", False)
    pd.set_option("display.max_columns", None)
    pd.set_option("display.max_colwidth", None)


def load_node_names():
    df = pd.read_csv(CAPABILITIES)
    ret = dict()
    for _id, node_id, labels in df[["node_id", "labels"]].itertuples():
        labels = str(labels).replace("[", "").replace("]", "").split(";")
        hostname = node_id
        for label in labels:
            if "hostname=" in label:
                (_token, hostname) = label.split("=")
        ret[node_id] = hostname
    return ret


def map_physical_to_node_id():
    df = pd.read_csv(MAPPING_TO_INSTANCE_ID)
    ret = dict()
    for _id, node_id, physical_id in df[["node_id", "physical_id"]].itertuples():
        ret[physical_id] = node_id
    return ret


def map_physical_to_workflow_id():
    df = pd.read_csv(MAPPING_TO_INSTANCE_ID)
    ret = dict()
    for _id, workflow_id, physical_id in df[
        ["workflow_id", "physical_id"]
    ].itertuples():
        ret[physical_id] = workflow_id
    return ret
