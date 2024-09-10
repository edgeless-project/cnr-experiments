#!/bin/bash

if [ "$NODES" == "" ] ; then
	echo "you must set the NODES environment variable"
	exit 1
fi

if [ "$EDGELESS_ROOT" == "" ] ; then
	echo "you must set the EDGELESS_ROOT environment variable"
	exit 1
fi

for node in $NODES ; do
	if [ "$COMMAND" == "status" ] ; then
		echo -n "$node: "
	fi
	ssh $node "COMMAND=$COMMAND ./node.sh"
done

exit 0
