# 004-delegated-small

## Scenario

Multiple instances of a workflow that computes the Fibonacci sequence, a CPU-intensive task. Additionally, edge nodes were shut down during the workflow execution to observe the behavior of the delegated orchestrator when nodes fail. The testbed used consisted of four nodes: one server node hosting the ε-ORC, the ε-CON, and the ancillary functions of the workflow, plus three heterogeneous edge nodes (a Raspberry Pi 3 Model 3B, an NVIDIA Jetson AGX Orin 64 GB, and an NVIDIA Jetson Xavier NX). All nodes used the WebAssembly run-time. The experiment lasts for approximately 470 s (around 8 minutes).

At 50 seconds into the experiment, we added one workflow every 5 seconds until 20 workflows were in the system, taking up to one minute for workflow creation.

Then we forced the following events:

- At 220 s we shut down the Orin node, which we resumed at 280 s.
- At 350 s we shut down the RPi node, which we resumed at 410 s.

## Repeatability

The `benchmark.sh` script can be used to create the workload, once the `$SERVER` environment variable is to the IP of the ε-CON.

However, manual intervention was required to stop/start the nodes at the specified times.

## Dataset

The datasets can be downloaded with:

```shell
../../scripts/download-artifacts.sh
```

After download, you can plot some basic metrics with the following scripts:

```shell
SHOW=1 python summary.py
```

```shell
SHOW=1 python transient.py
```

If needed, the required Python packages can be installed with `pip install -r requirements`.
