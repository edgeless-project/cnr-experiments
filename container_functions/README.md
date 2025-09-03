# EDGELESS container functions

Functions deployed to carry out experiments with the
[EDGELESS project](https://edgeless-project.eu/) by
[CNR-IIT](https://www.iit.cnr.it/en/).

## Instructions

Clone in the same directory this repo and EDGELESS:

```shell
git clone https://github.com/edgeless-project/edgeless.git
git clone https://github.com/edgeless-project/cnr-experiments.git
```

Install Rust:

```shell
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

Compile the function:

```shell
cd cnr-experiments/container_functions
cargo build --release
```

Build your Docker container, e.g., with an NVIDIA Jetson AGX Orin:

```shell
docker build -t double:latest -f Dockerfile.jetson .
```

Check that the container has been created:

```shell
docker image ls | grep double
```

Should return something like:

```text
double                    latest    2d83d0e50359   17 seconds ago   723MB
```