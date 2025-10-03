#!/usr/bin/env bash
# Main crontab script for daily shadow processing with parallel execution
# Refactored version - runs both road and noshadow stations in parallel
#
# Crontab entry:
# 0 0 * * * cd /mnt/drive/hirtst/DSM_DK; /mnt/drive/hirtst/terrain-shadow-processor/scripts/loke_shadows_daily_crontab.sh

set -e  # Exit on error

TODAY=$(date '+%Y%m%d')

# Activate Python environment
source /mnt/drive/hirtst/python-shadows/bin/activate

# Source environment configuration
source /mnt/drive/hirtst/terrain-shadow-processor/env.sh

echo "=============================================="
echo "Daily shadow processing (PARALLEL) on $TODAY"
echo "=============================================="
echo "Number of workers: ${NUM_WORKERS}"
echo "Batch size: ${BATCH_SIZE}"
echo ""

# Run the parallel processing script
cd /mnt/drive/hirtst/DSM_DK

/mnt/drive/hirtst/terrain-shadow-processor/scripts/daily_processing_parallel.sh

echo ""
echo "=============================================="
echo "Daily processing completed"
echo "=============================================="
