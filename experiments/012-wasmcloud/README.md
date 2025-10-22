# 012-wasmcloud

## Scenario



## wasmCloud set up

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
