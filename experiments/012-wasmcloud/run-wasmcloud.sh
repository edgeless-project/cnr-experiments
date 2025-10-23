#!/bin/bash

vec_sizes="1000 100000 1000000"

if [ "$BATCH_SIZE" == "" ] ; then
    BATCH_SIZE=5
fi
if [ "$NUM_BATCHES" == "" ] ; then
    NUM_BATCHES=10
fi
if [ "$BATCH_DURATION" == "" ] ; then
    BATCH_DURATION=60
fi
if [ "$INTER_TIME" == "" ] ; then
    INTER_TIME=0.1
fi

executables="client-wasmcloud.sh"
regular_files=""
outfile=data/wasmcloud/latencies.csv

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

print_header=1
for vec_size in $vec_sizes ; do
    echo "** vec_size $vec_size"
    name=0
    for (( batch = 0 ; batch < $NUM_BATCHES ; batch++ )) ; do
        echo -n "batch $batch: "
        for (( i = 0 ; i < $BATCH_SIZE ; i++ )) ; do
            OUTPUT_DIR=data/$vec_size\
                SIZE=$vec_size\
                NAME=$name\
                OPERATION=sin\
                INTER_TIME=0.1\
                ./client-wasmcloud.sh &
            name=$((name+1))
            echo -n "x"
        done
        echo ""
        sleep $BATCH_DURATION
    done

    echo "terminating"
    pkill -P $$
    sleep 1

    echo "aggregating datasets"
    for dataset in data/$vec_size/* ; do
        if [ $print_header -eq 1 ] ; then
            print_header=0
            cat $dataset >> $outfile
        else
            tail -n +2 $dataset >> $outfile
        fi
    done
   
    rm -rf data/$vec_size/ 2> /dev/null
done

