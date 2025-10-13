#!/usr/bin/env python
"""
Main script for running parallel shadow processing

This script orchestrates the parallel processing of station shadow calculations.
It can be called from the command line or from shell scripts.
"""
import os
import sys
import argparse
import logging
from datetime import datetime
from pathlib import Path

# Add src directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import parallel_grass_processor as pp
import shadow_functions as sf


def setup_main_logger(log_dir: str, process_type: str) -> str:
    """
    Set up the main logger for the processing run.

    Parameters
    ----------
    log_dir : str
        Directory for log files
    process_type : str
        Type of processing (road or noshadow)

    Returns
    -------
    str
        Path to the main log file
    """
    os.makedirs(log_dir, exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = os.path.join(log_dir, f'parallel_processing_{process_type}_{timestamp}.log')

    pp.setup_logger(log_file, outScreen=True)

    logger = logging.getLogger(__name__)
    logger.info(f"Starting parallel shadow processing for {process_type}")

    return log_file


def main():
    parser = argparse.ArgumentParser(
        description='Run parallel shadow calculations for road stations'
    )

    parser.add_argument(
        '--csv',
        type=str,
        required=True,
        help='CSV file with station data (easting|norting|station|county|roadsection)'
    )

    parser.add_argument(
        '--config',
        type=str,
        required=True,
        help='Configuration file (shadows_conf.ini)'
    )

    parser.add_argument(
        '--workers',
        type=int,
        default=None,
        help='Number of parallel workers (default: CPU count - 1)'
    )

    parser.add_argument(
        '--output-dir',
        type=str,
        required=True,
        help='Output directory for results'
    )

    parser.add_argument(
        '--log-dir',
        type=str,
        required=True,
        help='Directory for log files'
    )

    parser.add_argument(
        '--type',
        type=str,
        choices=['road', 'noshadow'],
        default='road',
        help='Type of processing (road or noshadow)'
    )

    parser.add_argument(
        '--tiles-dir',
        type=str,
        default=None,
        help='Directory containing DSM tiles (default: from env DSMPATH)'
    )

    parser.add_argument(
        '--grass-binary',
        type=str,
        default=None,
        help='Path to GRASS binary (default: from env GRASSBINARY)'
    )

    parser.add_argument(
        '--grass-settings',
        type=str,
        default=None,
        help='Path to GRASS settings (default: from env GRASSPROJECTSETTINGS)'
    )

    parser.add_argument(
        '--src-dir',
        type=str,
        default=None,
        help='Source directory with scripts (default: from env GITREPO)'
    )

    parser.add_argument(
        '--work-dir',
        type=str,
        default=None,
        help='Working directory for temporary files (default: current dir/work_TYPE)'
    )

    parser.add_argument(
        '--exit-on-grass-error',
        action='store_true',
        help='Exit immediately when a GRASS command fails (default: continue processing)'
    )

    args = parser.parse_args()


    # Set up main logger
    log_file = setup_main_logger(args.log_dir, args.type)
    logger = logging.getLogger(__name__)

    # Get environment variables or use defaults
    tiles_dir = args.tiles_dir or os.environ.get('DSMPATH', '/mnt/drive/hirtst/DSM_DK')
    grass_binary = args.grass_binary or os.environ.get('GRASSBINARY', '/usr/bin/grass78')
    grass_settings = args.grass_settings or os.environ.get(
        'GRASSPROJECTSETTINGS',
        '/mnt/drive/hirtst/terrain-shadow-processor/config/RoadStations'
    )
    src_dir = args.src_dir or os.environ.get('GITREPO', '/mnt/drive/hirtst/terrain-shadow-processor')

    # Validate inputs
    if not os.path.exists(args.csv):
        logger.error(f"CSV file not found: {args.csv}")
        sys.exit(1)

    if not os.path.exists(args.config):
        logger.error(f"Config file not found: {args.config}")
        sys.exit(1)

    # Create TIF file list if it doesn't exist
    tif_list_file = os.path.join(src_dir, 'list_of_tif_files.txt')
    if not os.path.exists(tif_list_file):
        logger.info(f"Creating TIF file list at {tif_list_file}")
        create_tif_file_list(tiles_dir, tif_list_file)

    # Create work directory (separate from TIF files and outputs)
    work_dir = args.work_dir or os.path.join(os.getcwd(), f'work_{args.type}')
    os.makedirs(work_dir, exist_ok=True)
    logger.info(f"Using work directory: {work_dir}")

    # Prepare configuration dictionary
    config = {
        'config_file': args.config,
        'tiles_dir': tiles_dir,
        'tif_list_file': tif_list_file,
        'grass_binary': grass_binary,
        'grass_settings': grass_settings,
        'python_binary': os.environ.get('PYBIN', sys.executable),
        'output_dir': args.output_dir,
        'log_dir': args.log_dir,
        'work_dir': work_dir,
        'src_dir': src_dir,
        'exit_on_grass_error': args.exit_on_grass_error
    }

    logger.info("Configuration:")
    for key, value in config.items():
        logger.info(f"  {key}: {value}")


    logger.info("Configuration:")
    for key, value in config.items():
        logger.info(f"  {key}: {value}")

    # Run parallel processing
    logger.info(f"Processing stations from {args.csv}")

    try:
        results = pp.parallel_process_with_grass(
            station_csv=args.csv,
            config=config,
            num_workers=args.workers
        )

        # Merge outputs
        logger.info("Merging batch outputs...")
        pp.merge_batch_outputs(results, args.output_dir)

        # Print summary
        success_count = sum(1 for r in results if r['status'] == 'success')
        failed_count = sum(1 for r in results if r['status'] == 'failed')
        total_stations = sum(r['stations_processed'] for r in results)

        logger.info("=" * 60)
        logger.info("Processing Summary:")
        logger.info(f"  Total batches: {len(results)}")
        logger.info(f"  Successful: {success_count}")
        logger.info(f"  Failed: {failed_count}")
        logger.info(f"  Stations processed: {total_stations}")
        logger.info(f"  Output directory: {args.output_dir}")
        logger.info(f"  Log file: {log_file}")
        logger.info("=" * 60)

        # Cleanup work directory
        import shutil
        if os.path.exists(work_dir):
            shutil.rmtree(work_dir)
            logger.info(f"Cleaned up work directory: {work_dir}")

        sys.exit(0 if failed_count == 0 else 1)

    except Exception as e:
        logger.error(f"Processing failed with error: {str(e)}", exc_info=True)
        sys.exit(1)


def create_tif_file_list(tiles_dir: str, output_file: str) -> None:
    """
    Create a list of available TIF files in the tiles directory.

    Parameters
    ----------
    tiles_dir : str
        Directory containing TIF files
    output_file : str
        Output file path
    """
    logger = logging.getLogger(__name__)

    if not os.path.exists(tiles_dir):
        logger.warning(f"Tiles directory does not exist: {tiles_dir}")
        # Create empty file
        with open(output_file, 'w') as f:
            pass
        return

    # Find all TIF files
    tif_files = []
    for root, dirs, files in os.walk(tiles_dir):
        for file in files:
            if file.endswith('.tif'):
                # Get just the filename, not the full path
                tif_files.append(file)

    logger.info(f"Found {len(tif_files)} TIF files in {tiles_dir}")

    # Write to file
    with open(output_file, 'w') as f:
        for tif_file in sorted(tif_files):
            f.write(f"{tif_file}\n")

    logger.info(f"Created TIF file list: {output_file}")


if __name__ == '__main__':
    main()
