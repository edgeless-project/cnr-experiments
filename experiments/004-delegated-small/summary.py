#!/usr/bin/env python3

import pandas as pd
import os
import matplotlib.pyplot as plt
import seaborn as sns

IMAGE_TYPE = os.environ.get("IMAGE_TYPE", "png")
DATASET = os.environ.get("DATASET", "conf/traces/health_status.csv")
SHOW = bool(os.environ.get("SHOW", ""))


def plot(df, x: str, y: str, hue: str | None, ylabel: str, show: bool, filename: str):
    fig, ax = plt.subplots()
    sns.boxplot(df, x=x, y=y, hue=hue, ax=ax)
    ax.set_ylabel(ylabel)
    ax.set_title("")
    fig.suptitle("")
    if show:
        plt.show(block=False)
    else:
        plt.savefig("{}.{}".format(filename, IMAGE_TYPE))


pd.set_option("display.show_dimensions", False)
pd.set_option("display.max_columns", None)
pd.set_option("display.max_colwidth", None)
df = pd.read_csv(DATASET)
df = df.replace(
    {
        "1e679b75-61b7-4674-aa91-6d88b12ba44a": "RPi",
        "f027aba4-008a-4b56-bd99-5c30694b20d4": "server",
        "6e8f107c-17ad-4488-9fd4-7d94dbfa7134": "Xavier",
        "4057b74e-ce7c-4df0-982d-eb20406d172e": "Orin",
    }
)

metrics = [
    ("proc_cpu_usage", "Process CPU usage"),
    ("load_avg_1", "Load average (1 minute)"),
]
for y, ylabel in metrics:
    plot(
        df,
        x="node_id",
        y=y,
        ylabel=ylabel,
        hue=None,
        show=SHOW,
        filename="{}-{}".format(os.path.basename(os.getcwd()), y),
    )

if SHOW:
    input("Press any key to continue")
