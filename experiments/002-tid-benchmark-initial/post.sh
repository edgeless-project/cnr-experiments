#!/bin/bash

names="small big"

for name in $names ; do
    echo "** $name"
    echo -n "workflow latency: "
    DATASET=dataset-$name/application_metrics.csv python wf_stats.py
    DATASET=dataset-$name/health_status.csv python health_stats.py
done
