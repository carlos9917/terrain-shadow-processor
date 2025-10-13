"""
Parallel GRASS processing using subprocess and GRASS batch mode

This approach:
1. Splits stations into batches
2. For each batch, creates a GRASS session
3. Runs the Python processing script inside GRASS as a batch job
4. Processes batches in parallel using subprocess
"""
import os
import sys
import logging
import pandas as pd
import subprocess
import tempfile
from typing import List, Dict, Tuple
from datetime import datetime
from multiprocessing import Pool, cpu_count

import shadow_functions as sf

logger = logging.getLogger(__name__)


def setup_logger(logfile: str, outScreen: bool = False) -> None:
    """Set up the logger output."""
    fmt_default = logging.Formatter(
        '%(levelname)-8s: %(asctime)s -- %(name)s: %(message)s'
    )

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    fh = logging.FileHandler(logfile, mode='w')
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(fmt_default)
    root_logger.addHandler(fh)

    if outScreen:
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        ch.setFormatter(fmt_default)
        root_logger.addHandler(ch)


def split_stations_by_batch(station_data: pd.DataFrame, num_batches: int) -> List[pd.DataFrame]:
    """Split station data into batches for parallel processing."""
    total_stations = len(station_data)
    batch_size = max(1, total_stations // num_batches)

    batches = []
    for i in range(0, total_stations, batch_size):
        batch = station_data.iloc[i:i + batch_size].copy()
        if not batch.empty:
            batches.append(batch)

    logger.info(f"Split {total_stations} stations into {len(batches)} batches")
    return batches


def process_batch_with_grass(args: Tuple) -> Dict:
    """
    Process a single batch using GRASS batch mode.

    This creates a GRASS session and runs the Python script inside it.
    """
    batch_df, batch_id, config = args

    log_file = os.path.join(config['log_dir'], f'batch_{batch_id}.log')

    # Create logger for this process
    setup_logger(log_file, outScreen=False)
    logger_batch = logging.getLogger(__name__)

    logger_batch.info(f"Batch {batch_id}: Starting with {len(batch_df)} stations")

    try:
        # Create temporary CSV for this batch
        batch_csv = os.path.join(config['work_dir'], f'batch_{batch_id}_stations.csv')
        with open(batch_csv, 'w') as f:
            for _, row in batch_df.iterrows():
                f.write(f"{row['easting']}|{row['norting']}|{row['station']}|{row['county']}|{row['roadsection']}\n")

        # Create output directory for this batch
        batch_output = os.path.join(config['output_dir'], f'batch_{batch_id}')
        os.makedirs(batch_output, exist_ok=True)

        # Create GRASS location for this batch
        grass_location = os.path.join(config['work_dir'], f'grassdata_batch_{batch_id}')

        # Initialize GRASS location with EPSG:25832
        logger_batch.info(f"Creating GRASS location at {grass_location}")

        # Copy template GRASS settings if available
        if os.path.exists(config['grass_settings']):
            import shutil
            shutil.copytree(config['grass_settings'], grass_location)
            logger_batch.info(f"Copied GRASS settings from {config['grass_settings']}")
        else:
            # Create new location with EPSG:25832
            cmd_create = f"{config['grass_binary']} --text -c EPSG:25832 {grass_location} -e"
            subprocess.check_output(cmd_create, shell=True, stderr=subprocess.STDOUT)
            logger_batch.info(f"Created GRASS location with EPSG:25832")

        # Create batch processing script that will run inside GRASS
        batch_script = os.path.join(config['work_dir'], f'run_batch_{batch_id}.sh')

        # Get absolute path to the process_batch_in_grass.py script
        batch_processor_script = os.path.join(config['src_dir'], 'src', 'process_batch_in_grass.py')

        # Verify the script exists
        if not os.path.exists(batch_processor_script):
            logger_batch.error(f"Batch processor script not found at: {batch_processor_script}")
            raise FileNotFoundError(f"process_batch_in_grass.py not found at {batch_processor_script}")

        logger_batch.info(f"Using batch processor script: {batch_processor_script}")

        # Build the command with optional exit-on-grass-error flag
        exit_on_error_flag = '--exit-on-grass-error' if config.get('exit_on_grass_error', False) else ''

        script_content = f"""#!/bin/bash
# GRASS batch job script for batch {batch_id}
cd {config['work_dir']}

{config['python_binary']} {batch_processor_script} \\
    --batch-csv {batch_csv} \\
    --config {config['config_file']} \\
    --output-dir {batch_output} \\
    --log-file {log_file} \\
    --tiles-dir {config['tiles_dir']} \\
    --tif-list {config['tif_list_file']} \\
    --batch-id {batch_id} {exit_on_error_flag}
"""


        with open(batch_script, 'w') as f:
            f.write(script_content)

        os.chmod(batch_script, 0o755)

        # Run GRASS with this batch script
        logger_batch.info(f"Starting GRASS batch job")

        env = os.environ.copy()
        env['GRASS_BATCH_JOB'] = batch_script

        cmd_grass = f"{config['grass_binary']} --text {grass_location}/PERMANENT"

        result = subprocess.run(
            cmd_grass,
            shell=True,
            env=env,
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            logger_batch.error(f"GRASS batch job failed: {result.stderr}")
            return {
                'batch_id': batch_id,
                'status': 'failed',
                'stations_processed': 0,
                'error': f"GRASS error: {result.stderr}"
            }

        # Cleanup
        import shutil
        if os.path.exists(grass_location):
            shutil.rmtree(grass_location)
        if os.path.exists(batch_csv):
            os.remove(batch_csv)
        if os.path.exists(batch_script):
            os.remove(batch_script)

        logger_batch.info(f"Batch {batch_id}: Completed successfully")

        return {
            'batch_id': batch_id,
            'status': 'success',
            'stations_processed': len(batch_df),
            'output_dir': batch_output,
            'error': None
        }

    except Exception as e:
        logger_batch.error(f"Batch {batch_id}: Exception: {str(e)}", exc_info=True)
        return {
            'batch_id': batch_id,
            'status': 'failed',
            'stations_processed': 0,
            'error': str(e)
        }


def parallel_process_with_grass(station_csv: str, config: Dict, num_workers: int = None) -> List[Dict]:
    """Process stations in parallel using GRASS batch mode."""

    if num_workers is None:
        num_workers = max(1, cpu_count() - 1)

    logger.info(f"Starting parallel GRASS processing with {num_workers} workers")

    # Read station data
    station_data = sf.read_stretch(station_csv)

    if station_data.empty:
        logger.error("No station data to process")
        return []

    # Split into batches
    batches = split_stations_by_batch(station_data, num_workers)

    # Prepare arguments for each batch
    batch_args = []
    for i, batch_df in enumerate(batches):
        batch_args.append((batch_df, i, config))

    # Process batches in parallel
    logger.info(f"Processing {len(batches)} batches in parallel")

    with Pool(processes=num_workers) as pool:
        results = pool.map(process_batch_with_grass, batch_args)

    # Summarize results
    total_success = sum(1 for r in results if r['status'] == 'success')
    total_failed = sum(1 for r in results if r['status'] == 'failed')
    total_stations = sum(r['stations_processed'] for r in results)

    logger.info(f"Parallel processing complete:")
    logger.info(f"  Successful batches: {total_success}")
    logger.info(f"  Failed batches: {total_failed}")
    logger.info(f"  Total stations processed: {total_stations}")

    return results


def merge_batch_outputs(results: List[Dict], final_output_dir: str) -> None:
    """Merge outputs from all batches into a single directory."""
    import shutil

    os.makedirs(final_output_dir, exist_ok=True)

    for result in results:
        if result['status'] == 'success':
            batch_output = result['output_dir']
            if os.path.exists(batch_output):
                for item in os.listdir(batch_output):
                    src = os.path.join(batch_output, item)
                    dst = os.path.join(final_output_dir, item)
                    if os.path.isfile(src):
                        shutil.copy2(src, dst)
                # Remove batch directory after merging
                shutil.rmtree(batch_output)

    logger.info(f"Merged all batch outputs to {final_output_dir}")
