#!/bin/bash

states="local remote"
vec_sizes="1 100 100000"
num_workflows="1 20"
executables="edgeless_cli"
regular_files="cli.toml trigger.wasm state_sim.wasm workflow-local.json workflow-remote.json"

if [ "$DURATION" == "" ] ; then
    DURATION=60
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

rm workflows.csv 2> /dev/null
for num_workflow in $num_workflows ; do
    for state in $states ; do
        for vec_size in $vec_sizes ; do
            outdir=data/$runtime-$num_workflow

            echo "*************************************************"
            echo "state $state, vec_size $vec_size, num_workflow $num_workflow"
            echo "*************************************************"

            sed -e "s/vec_size=10/vec_size=$vec_size/" \
                workflow-$state.json >  workflow.json

            ./edgeless_cli workflow stop all

            for (( i = 0 ; i < $num_workflow ; i++ )) ; do
                WF_ID=$(./edgeless_cli workflow start workflow.json)
                echo "$WF_ID,$state,$vec_size,$num_workflow" >> workflows.csv
            done

            sleep $DURATION
        done
    done
done

./edgeless_cli workflow stop all
rm workflow.json 2> /dev/null
