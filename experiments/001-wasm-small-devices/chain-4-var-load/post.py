#!/usr/bin/env python3

import pandas as pd

df = pd.read_csv("output.csv")

df_workflows = df[df["entity"] == "W"]
num_functions = \
    len(df[df["entity"] == "F"]["name"].unique()) \
    / len(df[df["entity"] == "W"]["name"].unique()) - 1
for node in df_workflows["node"].unique():
    with open(f"{node}.dat", "w", encoding="utf8") as outfile:
        for load in df_workflows["load"].unique():
            df_filtered = df_workflows.loc[
                (df_workflows["node"] == node) & (df_workflows["load"] == load)
            ]
            count = df_filtered.groupby("seed")["value"].count().sum()

            df_wf_lat = df_filtered.groupby("seed")["value"]
            mean_wf = df_wf_lat.mean()
            p025_wf = df_wf_lat.quantile(0.025)
            p975_wf = df_wf_lat.quantile(0.975)

            mean_func = df.loc[
                (df["entity"] == "F") & (df["node"] == node) & (df["load"] == load)
            ].groupby("seed")["value"].mean().values.mean()

            df_fun_lat = df.loc[
                (df["entity"] == "F") & (df["node"] == node) & (df["load"] == load)
            ].groupby("seed")["value"]
            mean_fun = df_fun_lat.mean()
            p025_fun = df_fun_lat.quantile(0.025)
            p975_fun = df_fun_lat.quantile(0.975)

            outfile.write(
                (
                    f"{load} {count}"
                    f" {mean_wf.values.mean() - mean_func * num_functions}"
                    f" {mean_wf.values.mean()}"
                    f" {p025_wf.values.mean()}"
                    f" {p975_wf.values.mean()}"
                    f" {mean_fun.values.mean()}"
                    f" {p025_fun.values.mean()}"
                    f" {p975_fun.values.mean()}\n"
                )
            )