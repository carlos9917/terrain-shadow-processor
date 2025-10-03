#!/usr/bin/env bash
# Quick test script with just 5 stations
set -e

echo "Creating test CSV with 5 stations..."
#head -5 /mnt/drive/hirtst/DSM_DK/station_data_20250824_utm.csv > /tmp/test_5_stations.csv
head -5 tests/station_data_20250824_utm.csv > /tmp/test_5_stations.csv

echo "Running parallel processing with 2 workers..."
source /mnt/drive/hirtst/python-shadows/bin/activate
source /mnt/drive/hirtst/terrain-shadow-processor/env.sh

$PYBIN /mnt/drive/hirtst/terrain-shadow-processor/src/run_parallel_processing.py \
    --csv /tmp/test_5_stations.csv \
    --config /mnt/drive/hirtst/terrain-shadow-processor/config/shadows_conf.ini \
    --workers 2 \
    --output-dir /tmp/test_output \
    --log-dir /tmp/test_logs \
    --tiles-dir ${DSMPATH} \
    --work-dir /tmp/test_work \
    --type road

echo ""
echo "Test completed!"
echo "Check results in: /tmp/test_output"
echo "Check logs in: /tmp/test_logs"
