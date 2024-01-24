#!/bin/bash

if [ "$MAX_WORKFLOW" == "" ] ; then
  MAX_WORKFLOW=10
fi

for (( i = 0 ; i < $MAX_WORKFLOW ; i++ )) ; do
  wf=wf$i
  avg=$(redis-cli get workflow:avg-latency:$wf | sed -e "s/\"//g")
  if [ "$avg" == "" ] ; then
    continue
  fi
  values=$(redis-cli --csv lrange workflow:latencies:$wf 0 -1 | sed -e "s/\"//g")
  echo "$wf [avg $avg] $values"
done
