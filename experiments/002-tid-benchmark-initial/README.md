# 002-tid-benchmark-initial

## Scenario

- ε-ORC, ε-CON, Redis in a VM
- nodes in other VMs:
  - 4small: 4 small-size (2 cores) nodes, with a `Random` allocation scheme
  - 4small-1big: same + 1 bigger (8 cores) node
  - 4small-1big-rr: same, but using a `RoundRobin` allocation scheme

Workload generated with `edgeless_benchmark`, see `run.sh` for the parameters.

## Repeatability

1. Install a Redis server
2. Update the ε-ORC and ε-CON configuration in `conf/`
3. Install a cluster of EDGELESS nodes
4. Use `run.sh` to run experiments by saving the output data in `dataset`

## Dataset

The datasets can be downloaded with:

```shell
../../scripts/download-artifacts.sh
```

After download, to print some post-processing statistics:

```shell
./post.sh
```