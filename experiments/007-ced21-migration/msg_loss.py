#!/usr/bin/env python3

import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from utils import show_or_save

DATA_DIR = os.environ.get("DATA_DIR", "data")
SHOW = bool(os.environ.get("SHOW", ""))

dfs = []
experiments = next(os.walk(DATA_DIR))[1]
losts = []
tots = []
for experiment in experiments:

    lost = 0
    tot = 0
    for filename in next(os.walk(f"{DATA_DIR}/{experiment}/"))[2]:
        if "output" not in filename:
            continue
        with open(f"{DATA_DIR}/{experiment}/{filename}", "r") as infile:
            last_value = None
            line_cnt = 0
            for line in infile:
                try:
                    value = int(line.rstrip().split(" ")[1])
                    if last_value == None:
                        last_value = value
                        continue
                    if value <= last_value:
                        raise RuntimeError
                    lost += (value - last_value) / 2 - 1
                    last_value = value
                    line_cnt += 1
                    tot += 1
                except:
                    print(
                        f"error in line {line_cnt} of file '{DATA_DIR}/{experiment}/{filename}': {line}"
                    )
                    raise

    losts.append(lost)
    tots.append(tot)

print(experiments)
print(losts)
print(tots)
loss_rates = [x / y for x, y in zip(losts, tots)]
print(loss_rates)

d = {
    "experiment": experiments,
    "loss": losts,
    "messages": tots,
    "loss_rate": loss_rates,
}

df = pd.DataFrame(data=d)

df["messages"] = df["messages"].apply(lambda x: x / 100)

metrics = [
    ("messages", "Total throughput (messages/s)"),
    ("loss_rate", "Message loss rate"),
]

basename = os.path.basename(os.getcwd())
for y, ylabel in metrics:
    fig, ax = plt.subplots()
    sns.barplot(df, x="experiment", y=y, ax=ax)
    ax.set_ylabel(ylabel)
    show_or_save("{}-{}".format(basename, y))

if SHOW:
    input("Press any key to continue")
