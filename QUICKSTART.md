# Quick Start Guide

## Running the Parallel Shadow Processing

### Option 1: Simple - Use the Helper Script (Recommended)

```bash
# Process a specific date with 4 workers (default)
/mnt/drive/hirtst/terrain-shadow-processor/scripts/run_single_date.sh 20250824

# Process with custom number of workers
/mnt/drive/hirtst/terrain-shadow-processor/scripts/run_single_date.sh 20250824 8
```

### Option 2: Manual - Direct Python Call

```bash
# Activate Python environment
source /mnt/drive/hirtst/python-shadows/bin/activate

# Load environment
source /mnt/drive/hirtst/terrain-shadow-processor/env.sh

# Run processing
$PYBIN /mnt/drive/hirtst/terrain-shadow-processor/src/run_parallel_processing.py \
    --csv /mnt/drive/hirtst/DSM_DK/station_data_20250824_utm.csv \
    --config /mnt/drive/hirtst/terrain-shadow-processor/config/shadows_conf.ini \
    --workers 4 \
    --output-dir /mnt/drive/hirtst/shadow_processing/output/road_20250824 \
    --log-dir /mnt/drive/hirtst/terrain-shadow-processor/logs \
    --tiles-dir /mnt/drive/hirtst/DSM_DK \
    --work-dir /mnt/drive/hirtst/shadow_processing/work/road_20250824 \
    --type road
```

### Option 3: Process Multiple Dates in a Loop

```bash
#!/bin/bash
source /mnt/drive/hirtst/terrain-shadow-processor/env.sh

# Process dates from Aug 20 to Aug 24
for date in 20250820 20250821 20250822 20250823 20250824; do
    echo "Processing $date..."
    /mnt/drive/hirtst/terrain-shadow-processor/scripts/run_single_date.sh $date 4
done
```

## Checking Results

### View Output Files
```bash
# List results
ls -lh /mnt/drive/hirtst/shadow_processing/output/road_20250824/

# Count output files
find /mnt/drive/hirtst/shadow_processing/output/road_20250824/ -name "lh_*.txt" | wc -l

# View a sample result file
head -50 /mnt/drive/hirtst/shadow_processing/output/road_20250824/lh_*.txt | head -1
```

### View Logs
```bash
# Main processing log
tail -100 /mnt/drive/hirtst/terrain-shadow-processor/logs/parallel_processing_road_*.log

# Individual batch logs
ls -lh /mnt/drive/hirtst/terrain-shadow-processor/logs/batch_*.log

# View specific batch
tail -50 /mnt/drive/hirtst/terrain-shadow-processor/logs/batch_0.log
```

### Monitor While Running
```bash
# In one terminal - run processing
/mnt/drive/hirtst/terrain-shadow-processor/scripts/run_single_date.sh 20250824 4

# In another terminal - monitor logs
tail -f /mnt/drive/hirtst/terrain-shadow-processor/logs/parallel_processing_road_*.log

# Or watch progress
watch -n 5 'find /mnt/drive/hirtst/shadow_processing/output/road_20250824/ -name "lh_*.txt" | wc -l'
```

## Performance Tuning

### Finding Optimal Worker Count

Test with different worker counts:
```bash
# Test with 2, 4, 8 workers
time /mnt/drive/hirtst/terrain-shadow-processor/scripts/run_single_date.sh 20250824 2
time /mnt/drive/hirtst/terrain-shadow-processor/scripts/run_single_date.sh 20250824 4
time /mnt/drive/hirtst/terrain-shadow-processor/scripts/run_single_date.sh 20250824 8
```

### Recommended Worker Counts

| System | Recommended Workers |
|--------|---------------------|
| 4 CPU cores | 3 workers |
| 8 CPU cores | 7 workers |
| 16 CPU cores | 15 workers |
| 32 CPU cores | 30 workers |

Generally: `num_workers = CPU_cores - 1`

## Troubleshooting

### File Not Found Error
```bash
# Check if CSV file exists
ls -l /mnt/drive/hirtst/DSM_DK/station_data_20250824_utm.csv

# If only .csv exists (not _utm.csv), you may need to convert it
# Check what files are available
ls -l /mnt/drive/hirtst/DSM_DK/station_data_20250824*
```

### No TIF Files Found
```bash
# Verify TIF files location
ls /mnt/drive/hirtst/DSM_DK/*.tif | head -5

# Update DSMPATH in env.sh if needed
nano /mnt/drive/hirtst/terrain-shadow-processor/env.sh
```

### Processing Hangs
```bash
# Check running processes
ps aux | grep python | grep run_parallel

# Check system resources
htop

# View log for errors
tail -100 /mnt/drive/hirtst/terrain-shadow-processor/logs/parallel_processing_road_*.log
```

### Out of Memory
```bash
# Reduce number of workers
/mnt/drive/hirtst/terrain-shadow-processor/scripts/run_single_date.sh 20250824 2
```

## Comparing with Original System

Run both and compare:

```bash
# Original system (sequential)
cd /mnt/drive/hirtst/DSM_DK
time ./daily_road_stations.sh

# New system (parallel with 4 workers)
time /mnt/drive/hirtst/terrain-shadow-processor/scripts/run_single_date.sh 20250824 4

# Compare output files
diff -r lh_500_0.4_11.25_00_*/ /mnt/drive/hirtst/shadow_processing/output/road_20250824/
```

## Example Session

Here's a complete example session:

```bash
# 1. Navigate to your working directory
cd /mnt/drive/hirtst/DSM_DK

# 2. Check available station data
ls -lh station_data_20250824*.csv

# 3. Run parallel processing with 4 workers
/mnt/drive/hirtst/terrain-shadow-processor/scripts/run_single_date.sh 20250824 4

# 4. Wait for completion (monitor in another terminal if desired)
# tail -f /mnt/drive/hirtst/terrain-shadow-processor/logs/parallel_processing_road_*.log

# 5. Check results
ls -lh /mnt/drive/hirtst/shadow_processing/output/road_20250824/

# 6. View sample output
head -50 /mnt/drive/hirtst/shadow_processing/output/road_20250824/lh_*.txt | head -1

# Done!
```

## Next Steps

After successful test run:

1. **Compare results** with original system
2. **Tune worker count** for your hardware
3. **Update crontab** for automated daily processing
4. **Set up monitoring** and alerts
5. **Configure backups** for output directory

See `README.md` for complete documentation.
