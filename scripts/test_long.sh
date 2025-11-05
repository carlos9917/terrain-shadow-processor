#!/usr/bin/env bash
# Quick test script with just 5 stations
set -e

CSV=/mnt/drive/hirtst/terrain-shadow-processor/tests/test_1e5_stations_utm.csv
NP=10
echo "Running parallel processing with $NP workers..."
source /mnt/drive/hirtst/python-shadows/bin/activate
source /mnt/drive/hirtst/terrain-shadow-processor/env.sh

$PYBIN /mnt/drive/hirtst/terrain-shadow-processor/src/run_parallel_processing.py \
    --csv $CSV \
    --config /mnt/drive/hirtst/terrain-shadow-processor/config/shadows_conf.ini \
    --workers $NP \
    --output-dir /mnt/drive/hirtst/terrain-shadow-processor/data \
    --log-dir /mnt/drive/hirtst/terrain-shadow-processor/logs \
    --tiles-dir ${DSMPATH} \
    --work-dir /tmp/test_work \
    --type road \
    --exit-on-grass-error

echo ""
echo "Test completed!"
echo "Check results in: /tmp/test_output"
echo "Check logs in: /tmp/test_logs"
