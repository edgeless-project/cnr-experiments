#!/bin/bash

vec_sizes="1000 100000 1000000"
vec_sizes="1000 1000000"

if [ "$BATCH_SIZE" == "" ] ; then
    BATCH_SIZE=5
fi
if [ "$NUM_BATCHES" == "" ] ; then
    NUM_BATCHES=10
fi
if [ "$BATCH_DURATION" == "" ] ; then
    BATCH_DURATION=60
fi

executables="edgeless_cli"
regular_files="cli.toml trigger.wasm state_sim.wasm workflow.json"
outfile=data/edgeless/workflows.csv

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

if [ -r $outfile ] ; then
    read -n 1 -p "file '$outfile' exists, hit Ctrl+C to leave or return to overwrite"
    rm $outfile 2> /dev/null
fi
mkdir -p $(dirname $outfile) 2> /dev/null

for vec_size in $vec_sizes ; do
    echo "** vec_size $vec_size"
    sed -e "s/vec_size=10/vec_size=$vec_size/" \
        workflow.json >  workflow-removeme.json
    ./edgeless_cli workflow stop all
    for (( batch = 0 ; batch < $NUM_BATCHES ; batch++ )) ; do
        echo -n "batch $batch: "
        for (( i = 0 ; i < $BATCH_SIZE ; i++ )) ; do
        
            WF_ID=$(./edgeless_cli workflow start workflow-removeme.json)
            echo "$WF_ID,$vec_size" >> $outfile

            echo -n "x"
        done
        echo ""
        sleep $BATCH_DURATION
    done

    echo "terminating"
    ./edgeless_cli workflow stop all
    sleep 1
done

rm workflow-removeme.json 2> /dev/null
