"""
Parallel processing module for shadow calculations

This module provides parallel processing capabilities using Python's multiprocessing.
It splits station lists into chunks and processes them in parallel.
"""
import os
import sys
import logging
import pandas as pd
import numpy as np
from multiprocessing import Pool, cpu_count, Manager
from typing import List, Dict, Tuple
from datetime import datetime
import tempfile
import subprocess

import shadow_functions as sf

logger = logging.getLogger(__name__)


def setup_logger(logfile: str, outScreen: bool = False) -> None:
    """
    Set up the logger output.

    Parameters
    ----------
    logfile : str
        Path to the log file
    outScreen : bool, optional
        Whether to also log to screen (default: False)
    """
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
    """
    Split station data into batches for parallel processing.

    Parameters
    ----------
    station_data : pd.DataFrame
        DataFrame containing station information
    num_batches : int
        Number of batches to split into

    Returns
    -------
    List[pd.DataFrame]
        List of DataFrames, each containing a subset of stations
    """
    total_stations = len(station_data)
    batch_size = max(1, total_stations // num_batches)

    batches = []
    for i in range(0, total_stations, batch_size):
        batch = station_data.iloc[i:i + batch_size].copy()
        if not batch.empty:
            batches.append(batch)

    logger.info(f"Split {total_stations} stations into {len(batches)} batches")
    return batches


def process_station_batch(args: Tuple) -> Dict:
    """
    Process a single batch of stations.

    This function is designed to be called by multiprocessing Pool.
    Each batch is processed in a separate GRASS GIS environment.

    Parameters
    ----------
    args : tuple
        Tuple containing (batch_df, batch_id, config_dict)

    Returns
    -------
    dict
        Dictionary with processing results
    """
    batch_df, batch_id, config_dict = args

    # Set up logging for this process
    log_file = os.path.join(config_dict['log_dir'], f'batch_{batch_id}.log')
    setup_logger(log_file, outScreen=False)

    logger.info(f"Batch {batch_id}: Starting processing of {len(batch_df)} stations")

    try:
        # Create temporary CSV file for this batch
        temp_csv = os.path.join(config_dict['work_dir'], f'batch_{batch_id}_stations.csv')

        # Write batch data to CSV in the expected format
        with open(temp_csv, 'w') as f:
            for _, row in batch_df.iterrows():
                f.write(f"{row['easting']}|{row['norting']}|{row['station']}|{row['county']}|{row['roadsection']}\n")

        # Read configuration
        shpars = sf.read_conf(config_dict['config_file'])

        # Process this batch
        stretch_data = sf.read_stretch(temp_csv)

        if stretch_data.empty:
            logger.warning(f"Batch {batch_id}: No valid station data")
            return {
                'batch_id': batch_id,
                'status': 'empty',
                'stations_processed': 0,
                'error': None
            }

        # Calculate tiles needed
        tiles_list = sf.calc_tiles(stretch_data)
        tif_files = sf.read_tif_list(config_dict['tif_list_file'])
        tiles_needed = sf.loop_tilelist(tiles_list, tif_files, config_dict['tiles_dir'])

        # Set up GRASS environment for this batch
        grass_project = os.path.join(
            config_dict['work_dir'],
            f'grassdata_batch_{batch_id}'
        )

        # Create output directory for this batch
        out_dir = os.path.join(
            config_dict['output_dir'],
            f'batch_{batch_id}'
        )
        os.makedirs(out_dir, exist_ok=True)

        # Set GRASS environment variables
        os.environ['GRASS_BATCH_JOB'] = ''

        # Initialize GRASS session
        setup_grass_environment(
            grass_project,
            config_dict['grass_settings'],
            config_dict['grass_binary'],
            shpars
        )

        # Process shadows for this batch
        sf.calc_shadows_single_station(stretch_data, tiles_needed, shpars, out_dir, shpars)

        # Cleanup GRASS project
        cleanup_grass_project(grass_project)

        # Remove temporary CSV
        if os.path.exists(temp_csv):
            os.remove(temp_csv)

        logger.info(f"Batch {batch_id}: Completed successfully, processed {len(stretch_data)} stations")

        return {
            'batch_id': batch_id,
            'status': 'success',
            'stations_processed': len(stretch_data),
            'output_dir': out_dir,
            'error': None
        }

    except Exception as e:
        logger.error(f"Batch {batch_id}: Failed with error: {str(e)}")
        return {
            'batch_id': batch_id,
            'status': 'failed',
            'stations_processed': 0,
            'error': str(e)
        }


def setup_grass_environment(grass_project: str, grass_settings: str,
                           grass_binary: str, shpars: Dict) -> None:
    """
    Set up a GRASS GIS environment for processing.

    Parameters
    ----------
    grass_project : str
        Path to GRASS project directory
    grass_settings : str
        Path to GRASS settings directory
    grass_binary : str
        Path to GRASS binary
    shpars : dict
        Shadow calculation parameters
    """
    import shutil

    # Create GRASS project directory
    os.makedirs(grass_project, exist_ok=True)

    # First, copy the template settings if they exist
    if os.path.exists(grass_settings):
        settings_permanent = os.path.join(grass_settings, 'PERMANENT')
        if os.path.exists(settings_permanent):
            # Copy entire PERMANENT directory structure
            permanent_dir = os.path.join(grass_project, 'PERMANENT')
            if os.path.exists(permanent_dir):
                shutil.rmtree(permanent_dir)
            shutil.copytree(settings_permanent, permanent_dir)
            logger.info(f"Copied GRASS settings from {grass_settings}")
        else:
            logger.warning(f"GRASS settings PERMANENT not found in {grass_settings}")
            # Create location with EPSG:25832 (ETRS89 / UTM zone 32N - Denmark)
            cmd = f'{grass_binary} --text -c EPSG:25832 {grass_project} -e'
            try:
                subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
                logger.info(f"Created GRASS project at {grass_project} with EPSG:25832")
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to create GRASS project: {e}")
                raise
    else:
        logger.warning(f"GRASS settings directory not found: {grass_settings}")
        # Create location with EPSG:25832
        cmd = f'{grass_binary} --text -c EPSG:25832 {grass_project} -e'
        try:
            subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
            logger.info(f"Created GRASS project at {grass_project} with EPSG:25832")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to create GRASS project: {e}")
            raise


def cleanup_grass_project(grass_project: str) -> None:
    """
    Clean up GRASS project directory.

    Parameters
    ----------
    grass_project : str
        Path to GRASS project directory
    """
    import shutil
    if os.path.exists(grass_project):
        try:
            shutil.rmtree(grass_project)
            logger.info(f"Cleaned up GRASS project at {grass_project}")
        except Exception as e:
            logger.warning(f"Failed to cleanup GRASS project: {e}")


def parallel_process_stations(station_csv: str, config: Dict, num_workers: int = None) -> List[Dict]:
    """
    Process stations in parallel using multiprocessing.

    Parameters
    ----------
    station_csv : str
        Path to CSV file containing station data
    config : dict
        Configuration dictionary
    num_workers : int, optional
        Number of parallel workers (default: CPU count - 1)

    Returns
    -------
    List[dict]
        List of result dictionaries from each batch
    """
    # Determine number of workers
    if num_workers is None:
        num_workers = max(1, cpu_count() - 1)

    logger.info(f"Starting parallel processing with {num_workers} workers")

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
        results = pool.map(process_station_batch, batch_args)

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
    """
    Merge outputs from all batches into a single directory.

    Parameters
    ----------
    results : List[dict]
        Results from parallel processing
    final_output_dir : str
        Final output directory
    """
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

    logger.info(f"Merged all batch outputs to {final_output_dir}")
