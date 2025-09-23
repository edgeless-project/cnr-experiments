#!/bin/bash

states="local remote"
vec_sizes="10 1000 100000"
num_workflows="20 200"
executables="edgeless_cli"
regular_files="cli.toml nodes trigger.wasm state_sim.wasm workflow-local.json workflow-remote.json"


if [ "$DURATION" == "" ] ; then
    DURATION=120
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
for state in $states ; do
    for num_workflow in $num_workflows ; do
        for vec_size in $vec_sizes ; do
            outdir=data/$runtime-$num_workflow

            echo "state $state, vec_size $vec_size, num_workflow $num_workflow"

            sed -e "s/vec_size=10/vec_size=$vec_size/" \
                workflow-$state.json >  workflow.json

            ./edgeless_cli workflow stop all >& /dev/null

            if [ "$state" == "local" ] ; then
                for (( i = 0 ; i < $num_workflow ; i++ )) ; do
                    WF_ID=$(./edgeless_cli workflow start workflow.json)
                    echo "$WF_ID,$state,$vec_size,$num_workflow" >> workflows.csv
                done
            else
                if [ "$state" == "remote" ] ; then
                    duration=$(( 100 * num_nodes / num_workflow ))
                fi
                for node in "${nodes[@]}" ; do
                    sed -e "s/e(100)/e($duration)/" workflow.json |\
                        sed -e "s/type=edge/hostname=$node/" workflow.json \
                        > workflow-node.json

                    WF_ID=$(./edgeless_cli workflow start workflow-node.json)
                    echo "$WF_ID,$state,$vec_size,$num_workflow" >> workflows.csv
                    rm workflow-node.json 2> /dev/null
                done
            fi

            sleep $DURATION
        done
    done
done

./edgeless_cli workflow stop all >& /dev/null
rm workflow.json 2> /dev/null
