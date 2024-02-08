#!/bin/bash

if [ "$NODE" == "" ] ; then
	echo "you must specify the NODE environment variable"
	exit 1
fi

address=$(hostname -i)
min_chain_size=5
max_chain_size=5
min_input_size=500
max_input_size=500
interarrival=0.5
wasm_path=../../../../edgeless/edgeless_benchmark/functions/vector_mul/vector_mul.wasm
redis_url=redis://127.0.0.1:6379/

loads="1 2 3 4 6 8 10 15 20 25 30"
min_seed=1
max_seed=10

for (( seed = $min_seed ; seed <= $max_seed ; seed++ )) ; do
for load in $loads ; do
	warmup=$(echo "$interarrival * $load" | bc)
	duration=$(echo "$warmup + 10" | bc)
	additional_fields="$(basename $PWD),$NODE,$load"
	additional_header="experiment,node,load"
	cmd="./edgeless_benchmark \
	  --wf-type \"vector-mul-chain;$min_chain_size;$max_chain_size;$min_input_size;$max_input_size;$wasm_path\" \
	  --orchestrator-url http://$address:7011 \
	  --controller-url http://$address:7001 \
	  --redis-url $redis_url \
	  --bind-address $address \
	  --interarrival $interarrival \
	  --arrival-model incr-and-keep \
	  --additional-fields $additional_fields \
	  --additional-header $additional_header \
	  --output output.csv \
	  --seed $seed \
	  --duration $duration \
	  --warmup $warmup \
	  --append \
	  "
	if [ "$DRY" != "" ] ; then
		echo $cmd
	else
		echo "node = $NODE, seed = $seed, load = $load"
		eval $cmd
		sleep 2
	fi
done
done
