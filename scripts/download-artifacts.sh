#!/bin/bash

pushd .. > /dev/null
experiment=$(basename $PWD)
popd > /dev/null
sub=$(basename $PWD)

if [ "$PRINT_ONLY" != "" ] ; then
  echo $experiment-$sub.tgz
  exit 0
fi

if [ -d data ] ; then
  echo "data directory already present: cowardly refusing to proceed"
  exit 1
fi

mkdir data 2> /dev/null
wget http://turig.iit.cnr.it/~claudio/public/edgeless/cnr-experiments/$experiment-$sub.tgz -O- | tar zx
