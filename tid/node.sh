#!/bin/bash

if [ "$COMMAND" == "" ] ; then
	COMMAND=status
fi

if [ "$COMMAND" == "status" ] ; then
	out=$(pgrep -l edgeless_node_d)
	if [ $? -eq 0 ] ; then
		echo "running"
	else
		echo "stopped"
	fi
elif [ "$COMMAND" == "start" ] ; then
	bin/edgeless_node_d -c bin/node.toml >& log &
elif [ "$COMMAND" == "stop" ] ; then
	killall edgeless_node_d
else
	echo "invalid COMMAND: $COMMAND"
	exit 1
fi
