#!/bin/bash

./edgeless_benchmark \
	-w 'map-reduce;map-reduce.json' \
	-c http://$CON_HOST:7001 \
	-d 86400 \
	-l 86400 \
	-i 600 \
	--arrival-model incremental \
	--seed 1
