# 007-ced21-migration

## Scenario

5 "edge" nodes with `RUST_WASM` and `CONTAINER` run-times, 1 "core" node with
a file-log resource and a `RUST_WASM` run-time.

Four batches:

- 1 workflow with WASM vs. CONTAINER function
- same with 10 workflows

The workflows generate 100 messages per second each.

The `mixer` utility is used to migrate every 1 seconds all the function 
instances from their hosting node to another randomly.

## Repeatability

Requirements:

- WASM functions: `double.wasm`, `trigger.wasm`

## Dataset

To replicate the experiments there must be a configured EDGELESS cluster.

The scripts assume that the orchestrator and controller run on the same host
that drives the experiments, which can be run with (follow interactive
instructions during execution):

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
python node_stats.py
```

```shell
python msg_loss.py
```

If needed, the required Python packages can be installed with
`pip install -r requirements`.
