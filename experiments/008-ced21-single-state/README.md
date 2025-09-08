# 008-ced21-single-state

## Scenario

5 "edge" nodes with `RUST_WASM` and `CONTAINER` run-times, 1 "core" node with
a file-log resource and a `RUST_WASM` run-time.

All possible combinations of:

- state type: local vs. remote (on Redis via the `redis` resource in the "core" node)
- state size: vectors of f32 numbers of size 10, 100, and 10000
- number of workflows: 1 vs. 20

The workflows generate 10 messages per second each.

## Repeatability

Requirements:

- WASM functions: `state_sim.wasm` (this repo), `trigger.wasm` (main repo,
  version 0.2)

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

After download, you can plot some basic metrics with the following script
(which produces PDF files):

```shell
python latency.py
```

If needed, the required Python packages can be installed with
`pip install -r requirements`.
