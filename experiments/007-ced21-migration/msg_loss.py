#!/usr/bin/env python3

import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from utils import show_or_save, pd_set_options, load_node_names

DATA_DIR = os.environ.get("DATA_DIR", "data")
SHOW = bool(os.environ.get("SHOW", ""))

dfs = []
experiments = next(os.walk(DATA_DIR))[1]
losts = []
for experiment in experiments:

    lost = 0
    for filename in next(os.walk(f"{DATA_DIR}/{experiment}/"))[2]:
        print(filename)
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
                    print(f"{experiment} {line_cnt} {value} {last_value}")
                    if value > last_value:
                        lost += (value - last_value) / 2 - 1
                    last_value = value
                    line_cnt += 1
                except:
                    print(
                        f"error in line {line_cnt} of file '{DATA_DIR}/{experiment}/{filename}': {line}"
                    )
                    raise

    losts.append(lost)

print(experiments)
print(losts)
assert False

df = pd.concat(
    [d.assign(experiment=name) for d, name in zip(dfs, experiments)],
    ignore_index=True,
)

metrics = [
    ("proc_cpu_usage", "Process CPU usage"),
    ("tot_throughput", "Network traffic per node (Mb/s)"),
    ("active_power", "Active power (mW)"),
]

basename = os.path.basename(os.getcwd())
for y, ylabel in metrics:
    fig, ax = plt.subplots()
    sns.boxplot(df, x="experiment", y=y, ax=ax)
    ax.set_ylabel(ylabel)
    show_or_save("{}-{}".format(basename, y))

if SHOW:
    input("Press any key to continue")
