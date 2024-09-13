#!/bin/bash

. environment

seeds="1"
orchestrations="Random RoundRobin"
interarrivals="60 30 20 10"

for seed in $seeds ; do
for orchestration in $orchestrations ; do
for interarrival in $interarrivals ; do

additional_fields=$orchestration,$interarrival
additional_header=orchestration,interarrival

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


git checkout head conf/orchestrator.toml
sed -i -e "s/@ORCHESTRATION_STRATEGY/$orchestration" conf/orchestrator.toml
sed -i -e "s/@ADDITIONAL_FIELDS/$seed,$additional_fields" conf/orchestrator.toml
sed -i -e "s/@ADDITIONAL_HEADER/seed,$additional_header" conf/orchestrator.toml
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
exit
RUST_LOG=info $EDGELESS_ROOT/target/release/edgeless_benchmark \
	--controller-url http://10.50.50.2:7001 \
	--orchestrator-url http://10.50.50.2:7011 \
	--bind-address 10.50.50.2 \
	--arrival-model poisson \
	--warmup 0 \
	--duration 3600 \
	--lifetime 300 \
	--interarrival $interarrival \
	--seed $seed \
	--wf-type "map-reduce;100;1900;0;0;1;4;1;4;5000;50000;0;0;$EDGELESS_ROOT/functions/" \
	--single-trigger-wasm $EDGELESS_ROOT/functions/single_trigger/single_trigger.wasm \
	--redis-url redis://127.0.0.1:6379/ \
	--dataset-path dataset/ \
	--append \
	--additional-fields "$additional_fields" \
	--additional-header "$additional_header"


COMMAND=stop ../../tid/nodes.sh
COMMAND=stop ../../tid/domain.sh
sleep 1

done
done
done
