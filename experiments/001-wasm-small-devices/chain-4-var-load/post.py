#!/usr/bin/env python3

import pandas as pd

df = pd.read_csv("output.csv")

df_workflows = df[df["entity"] == "W"]
for node in df_workflows["node"].unique():
    with open(f"{node}.dat", "w") as outfile:
        for load in df_workflows["load"].unique():
            df_filtered = df_workflows.loc[
                (df_workflows["node"] == node) & (df_workflows["load"] == load)
            ]
            count = df_filtered.groupby("seed")["value"].count().sum()
            mean = df_filtered.groupby("seed")["value"].mean()
            p025 = df_filtered.groupby("seed")["value"].quantile(0.025)
            p975 = df_filtered.groupby("seed")["value"].quantile(0.975)
            outfile.write(
                f"{load} {count} {mean.values.mean()} {p025.values.mean()} {p975.values.mean()}\n"
            )
