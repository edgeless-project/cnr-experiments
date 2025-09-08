#!/bin/bash

runtimes="wasm docker"
num_workflows="1 10"
executables="edgeless_benchmark mixer edgeless_cli"
regular_files="cli.toml trigger.wasm double.wasm workflow-docker.json workflow-wasm.json"

IP=$(hostname | cut -f 1 -d ' ')

echo "your IP is $IP"

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

./edgeless_cli workflow stop all

for runtime in $runtimes ; do
    for num_workflow in $num_workflows ; do
        outdir=data/$runtime-$num_workflow

        if [ -d $outdir ] ; then
            echo "directory $outdir already present: skipping"
            continue
        fi

        echo "*************************************************"
        echo "runtime $runtime, num_workflow $num_workflow"
        echo "*************************************************"

        RUST_LOG=info ./edgeless_benchmark \
            -w "json-spec;workflow-$runtime.json" \
            -c http://$IP:7001 \
            --arrival-model incr-and-keep \
            --warmup $num_workflow -i 1 -d $num_workflow -k

        ./mixer -c http://$IP:7001 -f double -l 'type=edge' -d 100 > mixer.log

        mkdir -p $outdir
        mv mixer.log $outdir

        ./edgeless_cli workflow stop all

        read -n 1 -p "move the output files to $outdir, then restart the orchestrator, and press a key..."
    done
done