#!/bin/bash

if [ ! -d data ] ; then
  mkdir data
fi

executables="../../viewer/target/release/viewer"

for executable in $executables ; do 
    if [ ! -x $executable ] ; then
        echo "cannot find executable in current directory: $executable"
        exit 1
    fi
done

../../viewer/target/release/viewer \
  --url http://0.0.0.0:3000/ \
  --output data/viewer.dat \
  --dry
