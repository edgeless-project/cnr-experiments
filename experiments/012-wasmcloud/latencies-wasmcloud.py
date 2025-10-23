#!/usr/bin/env python3

import os
import pandas as pd
from common import plot_latencies

HEALTH_STATUS = os.environ.get(
    "HEALTH_STATUS", "data/wasmcloud/dataset/health_status.csv"
)
CAPABILITIES = os.environ.get("CAPABILITIES", "data/wasmcloud/dataset/capabilities.csv")
WASM_CLOUD_LATENCIES = os.environ.get(
    "WASM_CLOUD_LATENCIES", "data/wasmcloud/latencies.csv"
)
IMAGE_TYPE = os.environ.get("IMAGE_TYPE", "pdf")

basename = os.path.basename(os.getcwd())

pd.set_option("display.show_dimensions", False)
pd.set_option("display.max_columns", None)
pd.set_option("display.max_colwidth", None)

df = pd.read_csv(WASM_CLOUD_LATENCIES)

plot_latencies(df, "wasmcloud")
