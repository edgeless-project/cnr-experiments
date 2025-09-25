# 011-multicore

## Scenario

Calibration scenario.

Single edge node.

Increasing number of workflows, 1 every 60 seconds.

The workflows generate 100 messages per second (function `trigger`), each
with a vector of 100k random elements, then the `state_sim` function computes
the sin().

## Repeatability

Requirements:

- WASM functions:
  - `state_sim.wasm` (this repo, version >= 0.2)
  - `trigger.wasm` (main repo, version >= 0.2)

The hostname of the node must be specified in the `nodes` file.

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
python workflow_latency.py
python node_health.py
python performance_samples.py
```

If needed, the required Python packages can be installed with
`pip install -r requirements`.
