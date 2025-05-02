#!/bin/bash
	
CON_URL=http://$CON_HOST:7001

echo "connecting to controller at $CON_URL"

./edgeless_benchmark \
	-w 'map-reduce;map-reduce.json' \
	-c $CON_URL \
	-d 7200 \
	-l 7200 \
	-i 30 \
	--arrival-model incremental \
	--seed 1
