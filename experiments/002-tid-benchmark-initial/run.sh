#!/bin/bash

. environment

echo "Deploying binaries to nodes"
../../tid/deploy.sh
if [ $? -ne 0 ] ; then
	exit 1
fi

echo "Stopping the domain services"
COMMAND=stop ../../tid/domain.sh
if [ $? -ne 0 ] ; then
	exit 1
fi
sleep 0.5

echo "Starting the domain services"
COMMAND=start ../../tid/domain.sh
if [ $? -ne 0 ] ; then
	exit 1
fi

echo "Stopping the nodes"
COMMAND=stop ../../tid/nodes.sh
if [ $? -ne 0 ] ; then
	exit 1
fi

echo "Starting the nodes"
COMMAND=start ../../tid/nodes.sh
if [ $? -ne 0 ] ; then
	exit 1
fi

echo "Starting the experiment"
RUST_LOG=info $EDGELESS_ROOT/target/release/edgeless_benchmark \
	--controller-url http://10.50.50.2:7001 \
	--orchestrator-url http://10.50.50.2:7011 \
	--bind-address 10.50.50.2 \
	--arrival-model poisson \
	--warmup 0 \
	--duration 3600 \
	--lifetime 600 \
	--interarrival 60 \
	--seed 1 \
	--wf-type "map-reduce;100;1900;0;0;1;4;1;4;5000;50000;0;0;$EDGELESS_ROOT/functions/" \
	--single-trigger-wasm $EDGELESS_ROOT/functions/single_trigger/single_trigger.wasm \
	--redis-url redis://127.0.0.1:6379/ \
	--dataset-path dataset/ \
	--append \
	--additional-fields "" \
	--additional-header ""


COMMAND=stop ../../tid/nodes.sh
COMMAND=stop ../../tid/domain.sh
