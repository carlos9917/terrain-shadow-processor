#!/usr/bin/env bash
# Script to run parallel processing for a specific date's station data
# Usage: ./run_single_date.sh YYYYMMDD [num_workers]
#
# Example: ./run_single_date.sh 20250824 4

set -e

# Check arguments
if [ -z "$1" ]; then
    echo "Usage: $0 YYYYMMDD [num_workers]"
    echo "Example: $0 20250824 4"
    exit 1
fi

DATE=$1
NUM_WORKERS=${2:-4}  # Default 4 workers

# Activate Python environment
echo "Activating Python environment..."
source /mnt/drive/hirtst/python-shadows/bin/activate

# Source environment configuration
echo "Loading environment configuration..."
source /mnt/drive/hirtst/terrain-shadow-processor/env.sh

# Override NUM_WORKERS if provided
export NUM_WORKERS=$NUM_WORKERS

# Set up directories
STATION_DATA_DIR=/mnt/drive/hirtst/DSM_DK
CSV_FILE=${STATION_DATA_DIR}/station_data_${DATE}_utm.csv

echo "=============================================="
echo "Running parallel shadow processing"
echo "Date: $DATE"
echo "Workers: $NUM_WORKERS"
echo "=============================================="
echo ""

# Check if CSV file exists
if [ ! -f "$CSV_FILE" ]; then
    echo "ERROR: CSV file not found: $CSV_FILE"
    echo ""
    echo "Available files:"
    ls -lh ${STATION_DATA_DIR}/station_data_${DATE}*.csv 2>/dev/null || echo "  No files found for date $DATE"
    exit 1
fi

# Check how many stations
NUM_STATIONS=$(wc -l < $CSV_FILE)
echo "Found $NUM_STATIONS stations to process"
echo "CSV file: $CSV_FILE"
echo ""

# Create output directories
mkdir -p ${WORKDIR}
mkdir -p ${OUTDIR}
mkdir -p ${LOGDIR}

echo "Directory configuration:"
echo "  TIF files: ${DSMPATH}"
echo "  Work dir:  ${WORKDIR}/road_${DATE}"
echo "  Output:    ${OUTDIR}/road_${DATE}"
echo "  Logs:      ${LOGDIR}"
echo ""

# Run the parallel processing
echo "Starting parallel processing..."
echo "----------------------------------------"

$PYBIN /mnt/drive/hirtst/terrain-shadow-processor/src/run_parallel_processing.py \
    --csv ${CSV_FILE} \
    --config /mnt/drive/hirtst/terrain-shadow-processor/config/shadows_conf.ini \
    --workers ${NUM_WORKERS} \
    --output-dir ${OUTDIR}/road_${DATE} \
    --log-dir ${LOGDIR} \
    --tiles-dir ${DSMPATH} \
    --work-dir ${WORKDIR}/road_${DATE} \
    --type road

echo ""
echo "=============================================="
echo "Processing completed!"
echo "=============================================="
echo ""
echo "Results saved to: ${OUTDIR}/road_${DATE}"
echo "Logs saved to:    ${LOGDIR}"
echo ""
echo "To view results:"
echo "  ls -lh ${OUTDIR}/road_${DATE}/"
echo ""
echo "To view logs:"
echo "  tail -100 ${LOGDIR}/parallel_processing_road_*.log"
echo ""
