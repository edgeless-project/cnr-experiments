#!/bin/bash

if [ "$NODES" == "" ] ; then
	echo "you must set the NODES environment variable"
	exit 1
fi

if [ "$EDGELESS_ROOT" == "" ] ; then
	echo "you must set the EDGELESS_ROOT environment variable"
	exit 1
fi

node_script=$(dirname $0)/node.sh
if [ ! -r "$node_script" ] ; then
	echo "could not read node.sh file from '$node_script'"
	exit 1
fi

for node in $NODES ; do
	echo $node
	rsync -Caz $node_script $node:~/
	rsync -Caz $EDGELESS_ROOT/target/release/edgeless_node_d $node:~/bin/
done
