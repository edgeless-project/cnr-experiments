#!/bin/bash

names="4small 4small-1big"

for name in $names ; do
    echo "** $name"
    echo -n "workflow latency: "
    DATASET=dataset-$name/application_metrics.csv python wf_stats.py
    echo -n "function execution time: "
    DATASET=dataset-$name/performance_samples.csv python exectime_stats.py
    DATASET=dataset-$name/health_status.csv python health_stats.py
done
