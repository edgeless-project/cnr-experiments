#!/bin/bash

cd /opt/edgeless/target/debug/
RUST_LOG=info ./edgeless_node_d -c $(hostname).toml >& $(hostname).log &
cd -
