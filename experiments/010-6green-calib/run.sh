#!/bin/bash

experiments="sin" # unsupported
vec_sizes="1000 10000 100000 1000000"
num_workflows="1 10"
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

rm workflows.csv 2> /dev/null
for experiment in $experiments ; do
    for num_workflow in $num_workflows ; do
        for vec_size in $vec_sizes ; do
            for node in "${nodes[@]}" ; do
                echo "experiment $experiment, vec_size $vec_size, num_workflow $num_workflow, node $node"

                sed -e "s/vec_size=10/vec_size=$vec_size/" workflow.json |\
                    sed -e "s/operation=sin/operation=$experiment/" |\
                    sed -e "s/type=edge/hostname=$node/" \
                    >  workflow.tmp.json

                ./edgeless_cli workflow stop all >& /dev/null

                for (( i = 0 ; i < $num_workflow ; i++ )) ; do
                    WF_ID=$(./edgeless_cli workflow start workflow.tmp.json)
                    echo "$WF_ID,$node,$vec_size,$num_workflow" >> workflows.csv
                done

                sleep $DURATION
            done
        done
    done
done

./edgeless_cli workflow stop all >& /dev/null
rm workflow.tmp.json 2> /dev/null
