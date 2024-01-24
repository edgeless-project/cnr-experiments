#!/bin/bash

if [ "$WORKFLOW" == "" ] ; then
  WORKFLOW=wf0
fi

if [ "$MAX_FUNCTION" == "" ] ; then
  MAX_FUNCTION=20
fi


wf=$WORKFLOW
avg=$(redis-cli get workflow:avg-latency:$wf | sed -e "s/\"//g")
if [ "$avg" == "" ] ; then
  exit
fi
values=$(redis-cli --csv lrange workflow:latencies:$wf 0 -1 | sed -e "s/\"//g")
echo "$wf [avg $avg] $values"

for (( i = 0 ; i < $MAX_FUNCTION ; i++ )) ; do
  avg=$(redis-cli get function:avg-latency:$wf:f$i | sed -e "s/\"//g")
  if [ "$avg" == "" ] ; then
    continue
  fi
  values=$(redis-cli --csv lrange function:latencies:$wf:f$i 0 -1 | sed -e "s/\"//g")
  echo "$wf f$i [avg $avg] $values"
done
