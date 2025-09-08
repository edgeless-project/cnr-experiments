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
