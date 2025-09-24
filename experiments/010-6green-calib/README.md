# 010-6green-calib

## Scenario

Calibration scenario.

2 "edge" nodes (1 Raspberry Pi 5, 1 NVIDIA AGX Orin) with a `RUST_WASM`
run-time, 1 "core" node with a `redis` resource and a `RUST_WASM` run-time.

Experiments are run for all possible combinations of:

- node type: RPi vs. Orin
- state: vectors of f32 numbers from 1k to 1M
- number of workflows: 1 vs. 10

Each experiment lasts 60 seconds.

The workflows generate 100 messages per second (function `trigger`).
When a message is received by the next function `state_sim`, it retrieves
the state (if not available it creates a new state with random numbers), then
computes the sin(), and saves it again.

## Repeatability

Requirements:

- WASM functions:
  - `state_sim.wasm` (this repo, version >= 0.2)
  - `trigger.wasm` (main repo, version >= 0.2)

The hostnames of the nodes must be specified in the `nodes` file, one host
per line.

## Dataset

To replicate the experiments there must be a configured EDGELESS cluster.

Assuming that there is a configured edgeless_cli in the current working
director, just hit:

```shell
./run.sh
```

The datasets obtained at CNR can be downloaded with:

```shell
../../scripts/download-artifacts.sh
```

After download, you can plot some basic metrics with the following scripts
(which produce PDF files):

```shell
python latency.py
python node_health.py
```

If needed, the required Python packages can be installed with
`pip install -r requirements`.
