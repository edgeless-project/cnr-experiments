#!/bin/bash

./edgeless_benchmark \
	-i 5 \
	--lifetime 86400 \
	-d 100 \
	--warmup 100 \
       	-w 'json-spec;workflow.json' \
	-c http://$SERVER:7001 \
	--arrival-model incremental \
	--keep-workflows
