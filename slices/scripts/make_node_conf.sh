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
	echo -n "making conf for $vm."
	IP=$(sudo multipass info $vm | grep ^IPv4 | sed -e "s/\s\+/ /g" | cut -f 2 -d ' ')
	echo "node_id = \"$(uuid)\"" > $vm.toml
	if [ "$DRY_RUN" == "" ] ; then
		grep orchestrator_url orchestrator.toml >> $vm.toml
		cat node.toml | grep -v ^node_id | grep -v ^orchestrator_url | sed -e "s/127.0.0.1/$IP/" >> $vm.toml
	fi
	echo ".done"
done
