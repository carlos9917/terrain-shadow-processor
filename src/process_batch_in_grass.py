#!/usr/bin/env python
"""
Process a single batch of stations within a GRASS GIS session.

This script is designed to be run as a GRASS_BATCH_JOB, meaning it will
be executed inside an active GRASS session where all GRASS commands are available.
"""
import os
import sys
import argparse
import logging

# Add src directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import shadow_functions as sf


def setup_logger(logfile):
    """Set up logging for this batch."""
    logging.basicConfig(
        filename=logfile,
        level=logging.DEBUG,
        format='%(levelname)-8s: %(asctime)s -- %(name)s: %(message)s'
    )


def main():
    parser = argparse.ArgumentParser(description='Process batch within GRASS session')
    parser.add_argument('--batch-csv', required=True, help='CSV file for this batch')
    parser.add_argument('--config', required=True, help='Configuration file')
    parser.add_argument('--output-dir', required=True, help='Output directory')
    parser.add_argument('--log-file', required=True, help='Log file')
    parser.add_argument('--tiles-dir', required=True, help='Directory with TIF files')
    parser.add_argument('--tif-list', required=True, help='File with list of TIF files')
    parser.add_argument('--batch-id', required=True, help='Batch ID')

    args = parser.parse_args()

    # Set up logging
    setup_logger(args.log_file)
    logger = logging.getLogger(__name__)

    logger.info(f"Batch {args.batch_id}: Starting processing within GRASS session")

    try:
        # Read configuration
        shpars = sf.read_conf(args.config)
        logger.info(f"Loaded configuration from {args.config}")

        # Read station data
        stretch_data = sf.read_stretch(args.batch_csv)
        if stretch_data.empty:
            logger.warning(f"Batch {args.batch_id}: No valid station data")
            sys.exit(0)

        logger.info(f"Batch {args.batch_id}: Processing {len(stretch_data)} stations")

        # Calculate tiles needed
        tiles_list = sf.calc_tiles(stretch_data)
        tif_files = sf.read_tif_list(args.tif_list)
        tiles_needed = sf.loop_tilelist(tiles_list, tif_files, args.tiles_dir)

        logger.info(f"Batch {args.batch_id}: Identified {len(tiles_needed)} tile-station combinations")

        # Create output directory
        os.makedirs(args.output_dir, exist_ok=True)

        # Set GRASS resolution (we're inside GRASS session now)
        sf.call_grass("set_resolution", shpars)

        # Process shadows
        sf.calc_shadows_single_station(stretch_data, tiles_needed, shpars, args.output_dir, shpars)

        logger.info(f"Batch {args.batch_id}: Completed successfully")

    except Exception as e:
        logger.error(f"Batch {args.batch_id}: Failed with error: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
