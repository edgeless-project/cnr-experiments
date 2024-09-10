#!/bin/bash

if [ "$EDGELESS_ROOT" == "" ] ; then
	echo "you must set the EDGELESS_ROOT environment variable"
	exit 1
fi

inabox_bin=$EDGELESS_ROOT/target/release/edgeless_inabox
if [ ! -e $inabox_bin ] ; then
	echo "cannot execute EDGELESS-in-a-box at '$inabox_bin'"
	exit 1
fi

if [ "$COMMAND" == "" ] ; then
	COMMAND=status
fi

if [ "$COMMAND" == "status" ] ; then
	out=$(pgrep -l edgeless_inabox)
	if [ $? -eq 0 ] ; then
		echo "running"
	else
		echo "stopped"
	fi
elif [ "$COMMAND" == "start" ] ; then
	cd conf && RUST_LOG=$RUST_LOG $inabox_bin 2>&1  >& log &
elif [ "$COMMAND" == "stop" ] ; then
	killall edgeless_inabox
else
	echo "invalid COMMAND: $COMMAND"
	exit 1
fi

exit 0
