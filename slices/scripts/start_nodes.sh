#!/bin/bash

if [ "$NODE_LOW" == "" ] ; then
	NODE_LOW=1
fi
if [ "$NODE_HIGH" == "" ] ; then
	NODE_HIGH=6
fi
if [[ $NODE_LOW -ge $NODE_HIGH ]] ; then
	echo "NODE_LOW should be smaller than NODE_HIGH: $NODE_LOW >= $NODE_HIGH"
	exit 1
fi

for (( i = $NODE_LOW ; i < $NODE_HIGH ; i++ )) ; do 
	vm=edge-$i
	echo "starting edgeless_node_d on $vm"
	if [ "$DRY_RUN" == "" ] ; then
		echo "/opt/edgeless/target/debug/run_node.sh" | sudo multipass shell $vm
	fi
done
