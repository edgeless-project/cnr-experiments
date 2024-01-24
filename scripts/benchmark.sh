#!/bin/bash

address=$(hostname -i)
min_chain_size=1
max_chain_size=5
min_matrix_size=10
max_matrix_size=20
interarrival=0
wasm_path=edgeless_benchmark/functions/matrix_mul/matrix_mul.wasm
redis_url=redis://127.0.0.1:6379/

target/debug/edgeless_benchmark \
  -w "matrix-mul-chain;$min_chain_size;$max_chain_size;$min_matrix_size;$max_matrix_size;$interarrival;$wasm_path;$redis_url" \
  -o http://$address:7011 \
  -c http://$address:7001 \
  -b $address \
  "$@"
