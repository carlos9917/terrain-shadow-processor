"""
Shadow calculation functions - Refactored for parallel processing

This module contains the core functions for shadow calculations using GRASS GIS.
Refactored from the original shadowFunctions.py to support parallel processing.
"""
import sqlite3
from datetime import datetime
import configparser
from collections import OrderedDict
import subprocess
import pandas as pd
import logging
import numpy as np
import os
from typing import Dict, List, Tuple, Optional

logger = logging.getLogger(__name__)
log_file_ts = datetime.strftime(datetime.now(), "%Y%m%d_%H%M%S")


def read_stretch(stretchfile: str) -> pd.DataFrame:
    """
    Read the station data from CSV file.

    Format: easting|norting|station|county|roadsection

    Parameters
    ----------
    stretchfile : str
        Path to the CSV file with station data

    Returns
    -------
    pd.DataFrame
        DataFrame with columns: easting, norting, station, county, roadsection, tile
    """
    data = pd.read_csv(stretchfile, sep='|', header=None, dtype=str)
    data.columns = ['easting', 'norting', 'station', 'county', 'roadsection']

    stretch_tile = []
    for k, nort in enumerate(data.norting):
        east = data.easting.values[k]
        stretch_tile.append('_'.join([
            str(int(float(nort) / 1000)),
            str(int(float(east) / 1000))
        ]))

    data['tile'] = stretch_tile
    logger.info(f"Read {len(data)} stations from {stretchfile}")
    return data


def read_conf(cfile: str) -> Dict[str, str]:
    """
    Read the configuration file.

    Parameters
    ----------
    cfile : str
        Path to the configuration file

    Returns
    -------
    dict
        Dictionary containing shadow calculation parameters
    """
    conf = configparser.RawConfigParser()
    conf.optionxform = str
    logger.info(f"Reading config file {cfile}")
    conf.read(cfile)

    secs = conf.sections()
    shadowPars = OrderedDict()
    for sec in secs:
        if sec == "SHADOWS":
            options = conf.options(sec)
            for param in options:
                paramValue = conf.get(sec, param)
                shadowPars[param] = paramValue

    return shadowPars


def call_grass(step: str, options: Dict, tile_data: Optional[Dict] = None, exit_on_error: bool = False, 
               log_dir: Optional[str] = None, batch_id: Optional[str] = None) -> Optional[bytes]:
    """
    Call GRASS GIS routines for various processing steps.

    Parameters
    ----------
    step : str
        The GRASS operation to perform
    options : dict
        Configuration options
    tile_data : dict, optional
        Data specific to the current tile being processed
    exit_on_error : bool, optional
        If True, raise exception on GRASS command failure. If False, log error and continue.
    log_dir : str, optional
        Directory to save grass_calls log files. If None, saves to current directory.
    batch_id : str, optional
        Batch identifier for unique log file naming

    Returns
    -------
    bytes or None
        Output from GRASS command for check_tile step, None otherwise
    """
    # Create unique log file name with batch ID if provided
    if batch_id is not None:
        log_file_name = f'grass_calls_batch_{batch_id}_{log_file_ts}.out'
    else:
        log_file_name = f'grass_calls_{log_file_ts}.out'
    
    # Use log_dir if provided, otherwise use current directory
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, log_file_name)
    else:
        log_file = log_file_name
    
    # Log the grass_calls file location on first use (only for import_tile step as an example)
    if step == 'import_tile':
        logger.info(f"GRASS commands are being logged to: {log_file}")

    def log_grass_error(error_msg: str, log_file: str, num_lines: int = 20):
        """Helper function to log error and show last lines of grass_calls file"""
        logger.error(f"{error_msg}. Check {log_file} for details.")
        # Try to read and log the last few lines of the grass_calls file
        try:
            if os.path.exists(log_file):
                with open(log_file, 'r') as f:
                    lines = f.readlines()
                    last_lines = lines[-num_lines:] if len(lines) > num_lines else lines
                    if last_lines:
                        logger.error(f"Last {len(last_lines)} lines from {log_file}:")
                        for line in last_lines:
                            logger.error(f"  {line.rstrip()}")
        except Exception as e:
            logger.error(f"Could not read grass_calls log file: {e}")

    if step == 'set_resolution':
        logger.info(f"Setting resolution {options['resolution']}")
        cmd = f'echo "call set_resol\\n" >> {log_file};g.region res={options["resolution"]} -p >> {log_file} 2>&1'
        try:
            out = subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True)
        except subprocess.CalledProcessError as err:
            log_grass_error(f"Setting resolution failed with error {err}", log_file)
            if exit_on_error:
                raise

    elif step == 'set_domain':
        logger.info(f"Setting domain {options['region']}")
        cmd = f'echo "call set_domain\\n" >> {log_file};g.region rast={options["region"]} res={options["resolution"]} -ap --verbose >> {log_file} 2>&1'
        try:
            out = subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True)
        except subprocess.CalledProcessError as err:
            log_grass_error(f"Setting domain failed with error {err}", log_file)
            if exit_on_error:
                raise

    elif step == 'check_tile':
        cmd = f'echo "call check_tile\\n" >> {log_file};g.list ras >> {log_file} 2>&1'
        logger.info(f"Checking tile {tile_data['surrounding_tile']}")
        try:
            out = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
            return out
        except subprocess.CalledProcessError as err:
            log_grass_error(f"Checking tile failed with error {err}", log_file)
            if exit_on_error:
                raise

    elif step == 'import_tile':
        logger.info(f"Importing file {tile_data['tif_file']}")
        logger.info(f"Output tile {tile_data['surrounding_tile']}")
        cmd = f'echo "call import_tile\\n" >> {log_file};r.in.gdal in={tile_data["tif_file"]} out={tile_data["surrounding_tile"]} -o memory=150 --verbose >> {log_file} 2>&1'
        try:
            out = subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True)
        except subprocess.CalledProcessError as err:
            log_grass_error(f"Importing tif file {tile_data['tif_file']} failed with error {err}", log_file)
            if exit_on_error:
                raise

    elif step == 'set_region':
        logger.info(f"Setting region {tile_data['region']}")
        cmd = f'echo "call set_region\\n" >> {log_file};g.region rast={tile_data["region"]} res={options["resolution"]} -ap --verbose >> {log_file} 2>&1'
        try:
            out = subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True)
        except subprocess.CalledProcessError as err:
            log_grass_error(f"Setting region {tile_data['region']} failed with error {err}", log_file)
            if exit_on_error:
                raise

    elif step == 'set_patch':
        logger.info(f"Setting patch {tile_data['region']}")
        cmd = f'echo "call set_patch\\n" >> {log_file};r.patch input={tile_data["region"]} output=work_domain --overwrite --verbose >> {log_file} 2>&1'
        try:
            out = subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True)
        except subprocess.CalledProcessError as err:
            log_grass_error(f"Setting region {tile_data['region']} failed with error {err}", log_file)
            if exit_on_error:
                raise

    elif step == 'calc_horizon':
        logger.info(f"Calculating horizon for {tile_data['coordinates_horizon']}")
        cmd = f'r.horizon -d elevation=work_domain step={options["horizonstep"]} maxdistance={options["maxdistance"]} coordinates={tile_data["coordinates_horizon"]} > {tile_data["out_file"]} 2>&1'
        try:
            out = subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True)
        except subprocess.CalledProcessError as err:
            log_grass_error(f"calc_horizon failed with error {err}", log_file)
            if exit_on_error:
                raise

    elif step == 'cleanup':
        logger.info("Cleanup region before processing next station")
        cmd = f'g.remove -f type=raster name=work_domain --verbose >> {log_file} 2>&1'
        try:
            out = subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True)
        except subprocess.CalledProcessError as err:
            log_grass_error(f"clean_up failed with error {err}", log_file)
            if exit_on_error:
                raise

    """
    Calculate shadows for stations in the given stretch data.

    This function processes all stations within a single tile.

    Parameters
    ----------
    stretch_data : pd.DataFrame
        Station data
    tiles_needed : pd.DataFrame
        Information about tiles needed for processing
    shpars : dict
        Shadow calculation parameters
    out_dir : str
        Output directory for results
    options : dict
        Additional processing options
    exit_on_error : bool, optional
        If True, raise exception on GRASS command failure
    log_dir : str, optional
        Directory to save grass_calls log files
    batch_id : str, optional
        Batch identifier for unique log file naming
    """
    for tile in stretch_data['tile'].values:
        logger.info(f"Processing tile: {tile}")

        select_surrounding_tiles = tiles_needed[tiles_needed['station_tile'] == tile]
        logger.info(f"Surrounding tiles: {select_surrounding_tiles['surrounding_tile'].tolist()}")

        ntiles = select_surrounding_tiles.shape[0]

        # Import surrounding tiles into GRASS
        tile_data = {}
        region_tiles = []

        for i, stile in enumerate(select_surrounding_tiles['surrounding_tile'].values):
            logger.info(f"Processing surrounding tile {stile}")
            tif_file = select_surrounding_tiles['tif_file'].values[i]
            tile_data['surrounding_tile'] = stile
            tile_data['tif_file'] = tif_file

            check_tile = call_grass('check_tile', shpars, tile_data, exit_on_error, log_dir, batch_id)
            call_grass('import_tile', shpars, tile_data, exit_on_error, log_dir, batch_id)
            region_tiles.append(stile)

        # Define region
        logger.info("Establishing working domain")
        tile_data = {}
        region = ','.join(region_tiles)
        tile_data['region'] = region

        # Establish the working domain
        call_grass('set_region', shpars, tile_data, exit_on_error, log_dir, batch_id)
        call_grass('set_patch', shpars, tile_data, exit_on_error, log_dir, batch_id)
        tile_data = {}

        # Process each station coordinate
        for stretch in set(select_surrounding_tiles['coords'].values):
            logger.info(f"Processing coordinates: {stretch}")
            station_id = stretch.split('|')[2]
            county = stretch.split('|')[3]
            roadsection = stretch.split('|')[4]

            tile_data['coordinates_horizon'] = stretch.split('|')[0] + ',' + stretch.split('|')[1]
            tile_data['out_file'] = os.path.join(
                out_dir,
                '_'.join(['lh', county, station_id, roadsection]) + '.txt'
            )
            tile_data['station_id'] = station_id

            call_grass('calc_horizon', shpars, tile_data, exit_on_error, log_dir, batch_id)

        # Cleanup after processing this tile
        call_grass('cleanup', shpars, tile_data, exit_on_error, log_dir, batch_id)



def calc_tiles(stretchlist: pd.DataFrame) -> OrderedDict:
    """
    Split the list of stations into their corresponding tiles.

    Parameters
    ----------
    stretchlist : pd.DataFrame
        Station data

    Returns
    -------
    OrderedDict
        Dictionary with tile names as keys and station lists as values
    """
    logger.info(f"Calculating tiles for {len(stretchlist)} stations")
    tiles_list = OrderedDict()

    for k, stretch in stretchlist.iterrows():
        insert = '|'.join([
            str(stretch['easting']),
            str(stretch['norting']),
            str(stretch['county']),
            str(stretch['station']),
            str(stretch['roadsection'])
        ])

        stretch_east = float(stretchlist['easting'][k])
        stretch_nort = float(stretchlist['norting'][k])
        stretch_tile = str(int(stretch_nort / 1000)) + '_' + str(int(stretch_east / 1000))

        if stretch_tile not in tiles_list:
            tiles_list[stretch_tile] = []

        tiles_list[stretch_tile].append(insert)

    logger.info(f"Created {len(tiles_list)} tiles")
    return tiles_list


def read_tif_list(tfile: str) -> np.ndarray:
    """
    Read list of available TIF files.

    Parameters
    ----------
    tfile : str
        Path to file containing list of TIF files

    Returns
    -------
    np.ndarray
        Array of TIF file names
    """
    tif_list = np.loadtxt(tfile, delimiter=' ', dtype=str)
    return tif_list


def loop_tilelist(list_tiles: OrderedDict, tif_files: np.ndarray, tif_dir: str) -> pd.DataFrame:
    """
    Calculate list of TIF files needed by the list of tiles.

    Parameters
    ----------
    list_tiles : OrderedDict
        Dictionary of tiles and their stations
    tif_files : np.ndarray
        Array of available TIF files
    tif_dir : str
        Directory containing TIF files

    Returns
    -------
    pd.DataFrame
        DataFrame with columns: station_tile, surrounding_tile, tif_file, coords
    """
    tileside = 1
    mindist = 1
    maxdistance = 1000
    dist = maxdistance / 1000

    ctiles_list = []
    tiles_list = []
    files_list = []
    coords_list = []

    for tkey in list_tiles.keys():
        east = int(tkey.split('_')[1])
        north = int(tkey.split('_')[0])

        tile_east = 1000 * (east + tileside)
        tile_west = 1000 * east
        tile_north = 1000 * (north + tileside)
        tile_south = 1000 * north

        if dist < 1:
            dist = mindist

        domain_east = tile_west / 1000 + dist
        domain_west = tile_west / 1000 - dist
        domain_north = tile_south / 1000 + dist
        domain_south = tile_south / 1000 - dist

        for tfile in tif_files:
            sw_corner_east = int(tfile.split('_')[3].replace('.tif', ''))
            sw_corner_north = int(tfile.split('_')[2])

            if (sw_corner_east <= domain_east and sw_corner_east >= domain_west and
                sw_corner_north <= domain_north and sw_corner_north >= domain_south):

                for coordinate in list_tiles[tkey]:
                    ctiles_list.append(tkey)
                    tiles_list.append('_'.join([str(sw_corner_north), str(sw_corner_east)]))
                    files_list.append(os.path.join(tif_dir, tfile))
                    coords_list.append(coordinate)

    data = pd.DataFrame({
        'station_tile': ctiles_list,
        'surrounding_tile': tiles_list,
        'tif_file': files_list,
        'coords': coords_list
    })

    logger.info(f"Identified {len(data)} tile-station combinations")
    return data
