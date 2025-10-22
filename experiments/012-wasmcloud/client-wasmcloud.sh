#!/bin/bash

if [ "$ENDPOINT" == "" ] ; then
    ENDPOINT=localhost:8000
fi
if [ "$NAME" == "" ] ; then
    NAME=Foo
fi
if [ "$SIZE" == "" ] ; then
    SIZE=1000
fi
if [ "$OPERATION" == "" ] ; then
    OPERATION=sin
fi
if [ "$INTER_TIME" == "" ] ; then
    INTER_TIME=0.1
fi
if [ "$OUTPUT_DIR" == "" ] ; then
    OUTPUT_DIR=data/wasm-cloud/$(date +%s)
fi

if [ ! -r $OUTPUT_DIR ] ; then
    mkdir -p $OUTPUT_DIR
fi

outfile=$OUTPUT_DIR/$NAME.csv

echo "timestamp,name,size,operation,inter-time,counter,latency" > $outfile

cnt=0
while true ; do
    timestamp=$(date +%s.%N)
    latency=$(curl --max-time 10 -s -w '%{time_total}\n' -o /dev/null "$ENDPOINT?name=$NAME,size=$SIZE,operation=$OPERATION,sleep=0")

    if [ $? -ne 0 ] ; then
        latency=-1
    fi

    echo "$timestamp,$NAME,$SIZE,$OPERATION,$INTER_TIME,$cnt,$latency" >> $outfile

    sleep $INTER_TIME
    
    cnt=$((cnt+1))
done