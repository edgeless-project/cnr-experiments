#!/bin/bash

benchmark_exec=../../../edgeless/target/release/edgeless_benchmark
cli_exec=../../../edgeless/target/release/edgeless_cli
executables="$benchmark_exec $cli_exec ./viewer.sh"
regular_files="workflow.json cli.toml"
outfile=data/benchmark.csv

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

echo "** start viewer"
./viewer.sh >& viewer.log &
PID=$!

echo "** make sure there are no workflows from previous experiments"
$cli_exec workflow stop all
sleep 1

$benchmark_exec \
  -c "http://172.20.1.3:7001" \
  --duration 300 \
  --lifetime 60 \
  --interarrival 2 \
  --arrival-model poisson  \
  --wf-type "json-spec;workflow.json" \
  --output data/benchmark.csv --append

echo "** stop viewer"
pkill -P $PID