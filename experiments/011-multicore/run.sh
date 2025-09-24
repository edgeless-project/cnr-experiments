#!/bin/bash

executables="edgeless_cli"
regular_files="cli.toml nodes trigger.wasm state_sim.wasm workflow.json"

if [ "$DURATION" == "" ] ; then
    DURATION=60
fi

readarray -t nodes < nodes
num_nodes="${#nodes[@]}"

if [ $num_nodes -le 0 ] ; then
    echo "the file 'nodes' should contain the hostnames of the edge hosts, one per line"
    exit 1
fi

for executable in $executables ; do 
    if [ ! -x $executable ] ; then
        echo "cannot find executable in current directory: $executable"
        exit 1
    fi
done

for regular_file in $regular_files ; do 
    if [ ! -r $regular_file ] ; then
        echo "cannot find file expected in current directory: $regular_file"
        exit 1
    fi
done

echo -n "waiting for all the nodes to be ready."
while true ; do
    ./edgeless_cli domain inspect all | grep ",$(( num_nodes + 1)) nodes," >& /dev/null
    if [ $? == 0 ] ; then
        break
    else
        sleep 0.1
        echo -n "."
    fi
done
echo ".done"

./edgeless_cli workflow stop all

for (( i = 0 ; i < 10 ; i++ )) ; do
    ./edgeless_cli workflow start workflow.json

    sleep $DURATION
done

./edgeless_cli workflow stop all
