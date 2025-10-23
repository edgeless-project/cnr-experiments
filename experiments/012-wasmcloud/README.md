# 012-wasmcloud

## Scenario

Comparison of EDGELESS vs. [wasmCloud](wasmcloud.dev) in handling a stateful
function.

### EDGELESS

- 5 Raspberry Pi 5 nodes with `RUST_WASM` run-time
- 1 VM with an node with a `RUST_WASM` run-time and ε-CON and ε-ORC (the latter
  saving samples from Proxy to a dataset)

Experiments are run for different state sizes.

In each experiment the number of workflows grows over time.

Each workflow remains active for the overall experiment duration and generates
10 messages per second (function `trigger`).
When a message is received by the next function `state_sim`, it
increments by 1.0 all the values.

#### EDGELESS requirements

WASM functions:

- `state_sim.wasm` (this repo)
- `trigger.wasm` (main repo, version 0.2)

### wasmCloud

Same as the EDGELESS scenario, but the functions are deployed on 5
wasmCloud nodes, which can autoscale up to 10 instances per node, and the
ingress load is balanced through an NGINX instance on the VM.

#### wasmCloud set up

Instructions to set up wasmCloud on a host:

```shell
curl https://sh.rustup.rs -sSf | sh
cargo install cargo-binstall
cargo binstall wash
rustup target add wasm32-wasip2
```

Create a default environment:

```shell
wash new component hello --template-name hello-world-rust
cd hello
wash dev
```

Copy the files from `wasmcloud` to the `hello` directory.

There must be a Redis server on localhost at the default port 6379.

Build with `wash build`, run node with `wash up` (`-d` for detached), and
deploy with `wash app deploy wadm.yaml`.

To verify from localhost you can use curl from a terminal:

```shell
curl "localhost:8000?name=Alice,size=1000,operation=sin,sleep=1000"
```

## Dataset

To replicate the experiments there must be a configured EDGELESS or wasmCloud
cluster:

```shell
./run-edgeless.sh
./run-wasmcloud.sh
```

The datasets obtained at CNR in two two cases can be downloaded with:

```shell
../../scripts/download-artifacts.sh
```

After download, you can plot some basic metrics with the following scripts
(which produce PDF files):

```shell
python latencies-edgeless.py
python node_health-edgeless.py
python latencies-wasmcloud.py
python node_health-wasmcloud.py
```

If needed, the required Python packages can be installed with
`pip install -r requirements`.


