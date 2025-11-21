# Scripts Documentation Report

## Overview

This document provides detailed documentation on how to use the scripts in the `scripts/` directory of the terrain-shadow-processor project. 
These scripts orchestrate the daily processing of shadow calculations for Danish road weather stations using Digital Surface Model (DSM) data and GRASS GIS.

---

## Table of Contents

1. [Main Production Scripts](#main-production-scripts)
   - [loke_shadows_daily_crontab.sh](#loke_shadows_daily_crontabsh)
   - [daily_processing_parallel.sh](#daily_processing_parallelsh)
   - [run_single_date.sh](#run_single_datesh)
2. [Testing Scripts](#testing-scripts)
   - [test_small.sh](#test_smallsh)
   - [test_long.sh](#test_longsh)
3. [Data Acquisition Scripts](#data-acquisition-scripts)
   - [get_data.sh](#get_datash)
   - [get_noshadow_stations.sh](#get_noshadow_stationssh)
4. [Utility Scripts](#utility-scripts)
   - [calcUTM.py](#calcutmpy)
   - [check_road_stations_dbase.py](#check_road_stations_dbasepy)
   - [search_zipfiles_nounzip.py](#search_zipfiles_nounzippy)
5. [Legacy Scripts](#legacy-scripts)
   - [daily_road_stations.sh](#daily_road_stationssh)

---

## Main Production Scripts

### loke_shadows_daily_crontab.sh

**Purpose**: Main entry point for automated daily shadow processing via cron job.

**Location**: `scripts/loke_shadows_daily_crontab.sh`

**Description**: 
This is the top-level script designed to be executed by cron for automated daily processing. It serves as a thin wrapper that sets up the environment and delegates to the parallel processing script.

**Key Features**:
- Designed for cron execution (runs at midnight daily)
- Sets up Python virtual environment
- Loads environment configuration
- Delegates to `daily_processing_parallel.sh` for actual processing
- Provides logging with timestamps

**Workflow**:
1. Activates Python environment at `/mnt/drive/hirtst/python-shadows/bin/activate`
2. Sources environment configuration from `env.sh`
3. Changes to data directory `/mnt/drive/hirtst/DSM_DK`
4. Executes `daily_processing_parallel.sh`
5. Logs completion status

**Crontab Entry**:
```bash
10 0 * * * cd /mnt/drive/hirtst/terrain-shadow-processor/scripts; ./loke_shadows_daily_crontab.sh
```

**Environment Variables Used**:
- `NUM_WORKERS`: Number of parallel workers (from env.sh)
- `BATCH_SIZE`: Batch size for processing (from env.sh)

**Exit Behavior**:
- Uses `set -e` to exit on any error
- Propagates errors from child scripts

**Dependencies**:
- Python virtual environment
- `env.sh` configuration file
- `daily_processing_parallel.sh`

---

### daily_processing_parallel.sh

**Purpose**: Core orchestration script for parallel shadow processing of both road and noshadow stations.

**Location**: `scripts/daily_processing_parallel.sh`

**Description**:
This is the main workhorse script that handles the complete daily processing workflow. It downloads station data, processes both road and noshadow stations in parallel, and handles post-processing including email notifications.

**Key Features**:
- Parallel processing of multiple station types
- Automatic data download from vejvejr.dk
- Organized directory structure management
- GRASS GIS environment setup
- Post-processing and email notifications
- Automatic cleanup of temporary files

**Workflow**:

#### Step 1: Data Download
- Executes `get_data.sh` to download road station data
  - Creates `station_data_YYYYMMDD_utm.csv`
- Executes `get_noshadow_stations.sh` to download stations without shadow data
  - Creates `station_noshadow_YYYYMMDD_utm.csv`

#### Step 2: Data Validation
- Checks if CSV files exist and contain data
- Counts number of stations to process
- Exits gracefully if no data available

#### Step 3: Environment Setup
- Creates directory structure:
  - `${WORKDIR}`: Temporary working directory
  - `${OUTDIR}`: Output directory for results
  - `${LOGDIR}`: Log directory
- Sets up GRASS GIS directories:
  - `${WORKDIR}/grassdata`: GRASS database
  - `$HOME/.grass7`: GRASS configuration
- Copies GRASS configuration from `config/RoadStations` and `config/rc_files`

#### Step 4: Parallel Processing

**Road Stations Processing**:
```bash
$PYBIN $GITREPO/src/run_parallel_processing.py \
    --csv ${STATION_DATA_DIR}/${csv_road} \
    --config $GITREPO/config/shadows_conf.ini \
    --workers ${NUM_WORKERS:-4} \
    --output-dir ${OUTDIR}/road_${today} \
    --log-dir ${LOGDIR} \
    --tiles-dir ${DSMPATH} \
    --work-dir ${WORKDIR}/road_${today} \
    --type road
```

**Noshadow Stations Processing**:
```bash
$PYBIN $GITREPO/src/run_parallel_processing.py \
    --csv ${STATION_DATA_DIR}/${csv_noshadow} \
    --config $GITREPO/config/shadows_conf.ini \
    --workers ${NUM_WORKERS:-4} \
    --output-dir ${OUTDIR}/noshadow_${today} \
    --log-dir ${LOGDIR} \
    --tiles-dir ${DSMPATH} \
    --work-dir ${WORKDIR}/noshadow_${today} \
    --type noshadow
```

#### Step 5: Post-Processing
- Prepares notification messages for new shadow data
- Generates email content using `prepare_message_newshadows.py`
- Sends email notifications via `email_new_shadows.py`
- Uses contact list from `email_scripts/contacts.txt`

#### Step 6: Cleanup
- Removes temporary working directories:
  - `${WORKDIR}/road_${today}`
  - `${WORKDIR}/noshadow_${today}`
- Removes temporary GRASS output files
- Preserves final results in `${OUTDIR}`

**Environment Variables**:
- `WORKDIR`: Temporary working directory
- `OUTDIR`: Output directory for results
- `LOGDIR`: Log directory
- `DSMPATH`: Path to DSM TIF files
- `GITREPO`: Path to git repository
- `PYBIN`: Python binary path
- `NUM_WORKERS`: Number of parallel workers (default: 4)

**Output Structure**:
```
${OUTDIR}/
├── road_YYYYMMDD/          # Road station results
├── noshadow_YYYYMMDD/      # Noshadow station results
├── deliver_station_data_YYYYMMDD.txt  # Notification message
└── email_YYYYMMDD          # Email content
```

**Error Handling**:
- Uses `set -e` for immediate exit on errors
- Validates data availability before processing
- Checks for required scripts before execution

---

### run_single_date.sh

**Purpose**: Manual execution script for processing a specific date's station data.

**Location**: `scripts/run_single_date.sh`

**Description**:
This script allows users to manually process shadow calculations for a specific date. It's useful for reprocessing historical data, testing, or catching up on missed processing runs.

**Usage**:
```bash
./run_single_date.sh YYYYMMDD [num_workers]
```

**Examples**:
```bash
# Process data for August 24, 2025 with default 4 workers
./run_single_date.sh 20250824

# Process with 8 workers for faster execution
./run_single_date.sh 20250824 8
```

**Arguments**:
- `$1` (required): Date in YYYYMMDD format
- `$2` (optional): Number of workers (default: 4)

**Key Features**:
- Flexible worker count configuration
- Detailed progress logging
- Pre-flight validation of input files
- Helpful error messages with file listings
- Directory structure verification

**Workflow**:

1. **Argument Validation**:
   - Checks if date argument is provided
   - Sets default worker count to 4 if not specified

2. **Environment Setup**:
   - Activates Python virtual environment
   - Sources environment configuration
   - Overrides `NUM_WORKERS` with command-line argument

3. **File Validation**:
   - Checks for existence of `station_data_${DATE}_utm.csv`
   - Counts number of stations to process
   - Lists available files if expected file not found

4. **Directory Creation**:
   - Creates `${WORKDIR}` for temporary files
   - Creates `${OUTDIR}` for results
   - Creates `${LOGDIR}` for logs

5. **Processing Execution**:
   - Runs `run_parallel_processing.py` with specified parameters
   - Processes only road stations (type: road)
   - Uses date-specific output directory

6. **Results Display**:
   - Shows output directory location
   - Shows log directory location
   - Provides commands to view results and logs

**Configuration Display**:
The script displays comprehensive configuration information:
```
==============================================
Running parallel shadow processing
Date: 20250824
Workers: 4
==============================================

Found 150 stations to process
CSV file: /mnt/drive/hirtst/DSM_DK/station_data_20250824_utm.csv

Directory configuration:
  TIF files: ${DSMPATH}
  Work dir:  ${WORKDIR}/road_20250824
  Output:    ${OUTDIR}/road_20250824
  Logs:      ${LOGDIR}
```

**Output Information**:
After completion, provides helpful commands:
```
Results saved to: ${OUTDIR}/road_20250824
Logs saved to:    ${LOGDIR}

To view results:
  ls -lh ${OUTDIR}/road_20250824/

To view logs:
  tail -100 ${LOGDIR}/parallel_processing_road_*.log
```

**Error Handling**:
- Exits with usage message if date not provided
- Exits with error if CSV file not found
- Lists available files for the date if expected file missing
- Uses `set -e` to exit on any processing error

**Use Cases**:
1. **Reprocessing**: Reprocess data for a specific date after fixes
2. **Catch-up**: Process missed dates due to system downtime
3. **Testing**: Test processing with production data
4. **Performance Tuning**: Experiment with different worker counts

---

## Testing Scripts

### test_small.sh

**Purpose**: Quick test script for validating the processing pipeline with a small dataset.

**Location**: `scripts/test_small.sh`

**Description**:
This script is designed for rapid testing and validation of the shadow processing pipeline. It processes a small subset of stations (100 stations) with minimal resources to quickly verify that the system is working correctly.

**Key Features**:
- Fast execution (processes only 100 stations)
- Uses temporary directories for output
- Minimal resource usage (2 workers)
- Ideal for development and debugging

**Workflow**:

1. **Test Data Preparation**:
   - Extracts first 100 lines from test CSV file
   - Creates temporary test file: `/tmp/test_5_stations.csv`
   - Source: `tests/station_data_20250824_utm.csv`

2. **Environment Setup**:
   - Activates Python virtual environment
   - Sources environment configuration

3. **Processing Execution**:
   - Runs with 2 workers for quick testing
   - Uses temporary directories:
     - Output: `/tmp/test_output`
     - Logs: `/tmp/test_logs`
     - Work: `/tmp/test_work`
   - Processes as road station type

**Command Executed**:
```bash
$PYBIN /mnt/drive/hirtst/terrain-shadow-processor/src/run_parallel_processing.py \
    --csv /tmp/test_5_stations.csv \
    --config /mnt/drive/hirtst/terrain-shadow-processor/config/shadows_conf.ini \
    --workers 2 \
    --output-dir /tmp/test_output \
    --log-dir /tmp/test_logs \
    --tiles-dir ${DSMPATH} \
    --work-dir /tmp/test_work \
    --type road
```

**Output**:
```
Test completed!
Check results in: /tmp/test_output
Check logs in: /tmp/test_logs
```

**Use Cases**:
- Quick validation after code changes
- Testing configuration changes
- Debugging processing issues
- Verifying GRASS GIS setup
- Development workflow testing

**Expected Runtime**: 
- Approximately 1-5 minutes depending on system

---

### test_long.sh

**Purpose**: Extended test script for performance testing and validation with larger datasets.

**Location**: `scripts/test_long.sh`

**Description**:
This script performs more comprehensive testing with a larger dataset (100,000 stations) and more workers. It's designed for performance testing, stress testing, and validating the system under production-like loads.

**Key Features**:
- Large dataset testing (100,000 stations)
- High parallelization (10 workers)
- Exit on GRASS errors for strict validation
- Performance benchmarking capability

**Workflow**:

1. **Environment Setup**:
   - Activates Python virtual environment
   - Sources environment configuration

2. **Processing Execution**:
   - Uses test file: `tests/test_1e5_stations_utm.csv`
   - Runs with 10 workers for parallel processing
   - Enables `--exit-on-grass-error` flag for strict error checking

**Command Executed**:
```bash
$PYBIN /mnt/drive/hirtst/terrain-shadow-processor/src/run_parallel_processing.py \
    --csv /mnt/drive/hirtst/terrain-shadow-processor/tests/test_1e5_stations_utm.csv \
    --config /mnt/drive/hirtst/terrain-shadow-processor/config/shadows_conf.ini \
    --workers 10 \
    --output-dir /mnt/drive/hirtst/terrain-shadow-processor/data \
    --log-dir /mnt/drive/hirtst/terrain-shadow-processor/logs \
    --tiles-dir ${DSMPATH} \
    --work-dir /tmp/test_work \
    --type road \
    --exit-on-grass-error
```

**Configuration**:
- Workers: 10 (configurable via `NP` variable)
- CSV: 100,000 test stations
- Exit on GRASS error: Enabled

**Output**:
```
Test completed!
Check results in: /tmp/test_output
Check logs in: /tmp/test_logs
```

**Use Cases**:
- Performance benchmarking
- Stress testing the parallel processing system
- Validating system stability under load
- Testing resource utilization
- Pre-production validation

**Expected Runtime**: 
- Several hours depending on system resources and DSM data availability

**Note**: The script comment says "5 stations" but actually processes 100,000 stations from the test file.

---

## Data Acquisition Scripts

### get_data.sh

**Purpose**: Downloads and processes road station data from vejvejr.dk server.

**Location**: `scripts/get_data.sh`

**Description**:
This script is responsible for acquiring the daily list of road weather stations from the vejvejr.dk service. It downloads station data including coordinates and converts them from latitude/longitude to UTM coordinates.

**Key Features**:
- Automated data download from vejvejr.dk
- Character encoding conversion (ISO-8859-1 to UTF-8)
- Coordinate conversion to UTM
- Support for both download and conversion-only modes

**Workflow**:

#### Mode 1: Download and Convert (No Arguments)
1. **Download Station Data**:
   - Connects to `http://vejvejr.dk/glatinfoservice/GlatInfoServlet?command=stationlist`
   - Uses credentials: `--user=vejvejr --password=settings`
   - Downloads to temporary file `out.tmp`

2. **Character Encoding Conversion**:
   - Converts from ISO-8859-1 to UTF-8
   - Handles Danish characters (æ, ø, å)
   - Saves as `station_data_YYYYMMDD.csv`

3. **Coordinate Conversion**:
   - Calls `calcUTM.py` to convert lat/lon to UTM
   - Creates `station_data_YYYYMMDD_utm.csv`

#### Mode 2: Convert Only (With Argument)
- If CSV file provided as argument
- Skips download step
- Only performs UTM conversion

**Usage**:
```bash
# Download and convert
./get_data.sh

# Convert existing file only
./get_data.sh existing_file.csv
```

**Environment Setup**:
- Activates Python environment: `/mnt/drive/hirtst/python-shadows/bin/activate`
- Sources configuration: `/mnt/drive/hirtst/terrain-shadow-processor/env.sh`

**Output Files**:
- `station_data_YYYYMMDD.csv`: Raw downloaded data (lat/lon)
- `station_data_YYYYMMDD_utm.csv`: Converted data (UTM coordinates)

**Data Format**:
Input CSV format:
```
station_id,"Location Name",longitude,latitude
5160,"Gjørup",9.36827374,56.65630341
```

Output CSV format (pipe-delimited):
```
easting|norting|station|roadsection|county
523456.789|6234567.890|5160|0|0
```

**Error Handling**:
- Removes temporary files after processing
- Character encoding issues handled by iconv

---

### get_noshadow_stations.sh

**Purpose**: Downloads and processes stations that are missing shadow data.

**Location**: `scripts/get_noshadow_stations.sh`

**Description**:
This script specifically retrieves stations that don't have shadow calculations yet. It's used to identify and process new stations or stations where shadow data needs to be regenerated.

**Key Features**:
- Targeted download of stations without shadow data
- Server failover capability
- Data validation and error checking
- Character encoding conversion
- UTM coordinate conversion with noshadow format

**Workflow**:

#### Mode 1: Download and Convert (No Arguments)

1. **Server Configuration**:
   - Primary server: `vejvejr.dk`
   - Backup server: `gimli:8081` (commented out)

2. **Download Station Data**:
   - URL: `http://vejvejr.dk/glatinfoservice/GlatInfoServlet?command=stationlist&formatter=glatmodel&noshadow=true`
   - Credentials: `--user=vejvejr --password=settings`
   - Downloads to temporary file `out.tmp`

3. **Download Validation**:
   - Checks wget return code
   - Exits with error if download fails
   - Validates that CSV file is not empty

4. **Character Encoding Conversion**:
   - Converts from ISO-8859-1 to UTF-8
   - Handles Danish characters
   - Saves as `station_noshadow_YYYYMMDD.csv`

5. **Empty File Check**:
   - Verifies CSV file has content
   - Exits with error if file is empty

6. **Coordinate Conversion**:
   - Calls `calcUTM.py` with `noshadow` format
   - Creates `station_noshadow_YYYYMMDD_utm.csv`

#### Mode 2: Convert Only (With Argument)
- If CSV file provided as argument
- Skips download step
- Only performs UTM conversion

**Usage**:
```bash
# Download and convert
./get_noshadow_stations.sh

# Convert existing file only
./get_noshadow_stations.sh existing_file.csv
```

**Environment Setup**:
- Activates Python environment: `/mnt/drive/hirtst/python-shadows/bin/activate`
- Sources configuration: `/mnt/drive/hirtst/terrain-shadow-processor/env.sh`

**Output Files**:
- `station_noshadow_YYYYMMDD.csv`: Raw downloaded data
- `station_noshadow_YYYYMMDD_utm.csv`: Converted data with UTM coordinates

**Data Format**:
Input CSV format (noshadow):
```
station_id,"Location Name",sensor1,sensor2,sensor3,longitude,latitude
4031,"Aarhus-Nord",0,0,0,10.111693,56.21921
```

Output CSV format (pipe-delimited):
```
easting|norting|station|sensor1|sensor2
567890.123|6234567.890|4031|0|0
```

**Error Handling**:
- Checks wget return code
- Validates file is not empty
- Exits with descriptive error messages
- Removes temporary files

**Special Features**:
- The `noshadow=true` parameter filters for stations without shadow data
- Includes sensor information (sensor1, sensor2, sensor3)
- Different output format than road stations

---

## Utility Scripts

### calcUTM.py

**Purpose**: Converts geographic coordinates (latitude/longitude) to UTM (Universal Transverse Mercator) coordinates.

**Location**: `scripts/calcUTM.py`

**Description**:
This Python script handles coordinate transformation from ETRS89 (EPSG:4258) latitude/longitude to UTM Zone 32N (EPSG:25832). It supports both command-line coordinate conversion and batch file processing with two different input formats.

**Key Features**:
- Single coordinate conversion
- Batch file processing
- Two input formats: road_stretch and noshadow
- High-precision coordinate transformation
- Pandas-based CSV processing

**Coordinate Systems**:
- **Input**: ETRS89 (EPSG:4258) - European Terrestrial Reference System 1989
- **Output**: UTM Zone 32N (EPSG:25832) - Universal Transverse Mercator, Zone 32 North
- **Precision**: 6 decimal places for input, 3 decimal places for output

**Functions**:

#### `read_data_noshadow(ifile)`
Reads station data in noshadow format.

**Input Format**:
```csv
4031,"Aarhus-Nord",0,0,0,10.111693,56.21921
```

**Columns**: station, location, sensor1, sensor2, sensor3, lon, lat

**Returns**: Pandas DataFrame

#### `read_data_road_stretch(ifile)`
Reads station data in road stretch format.

**Input Format**:
```csv
5160,"Gjørup",9.36827374,56.65630341
```

**Columns**: station, location, lon, lat

**Returns**: Pandas DataFrame

#### `latlon2utm(lat, lon)`
Converts a single lat/lon coordinate pair to UTM.

**Parameters**:
- `lat`: Latitude in decimal degrees
- `lon`: Longitude in decimal degrees

**Returns**: Tuple of (easting, northing) as strings with 6 decimal places

**Implementation**:
```python
from pyproj import Transformer
transformer = Transformer.from_crs(4258, 25832, always_xy=True)
for pt in transformer.itransform([(float(lon), float(lat))]): 
    res = '{:.6f} {:.6f}'.format(*pt)
east, north = res.split()
return east, north
```

#### `calc_UTM_file(ifile, input_format="road_stretch")`
Processes an entire CSV file and converts all coordinates.

**Parameters**:
- `ifile`: Input CSV file path
- `input_format`: Either "road_stretch" or "noshadow"

**Output Format (road_stretch)**:
```
easting|norting|station|roadsection|county
523456.789|6234567.890|5160|0|0
```

**Output Format (noshadow)**:
```
easting|norting|station|sensor1|sensor2
567890.123|6234567.890|4031|0|0
```

**Output File**: Input filename with `_utm.csv` suffix

**Usage**:

#### Command Line - Single Coordinate
```bash
python calcUTM.py -coords 56.21921,10.111693
```

**Output**:
```
567890.123456 6234567.890123
```

#### Command Line - File Processing (Road Stretch)
```bash
python calcUTM.py -ifile station_data_20250824.csv
```

**Output**: Creates `station_data_20250824_utm.csv`

#### Command Line - File Processing (Noshadow)
```bash
python calcUTM.py -ifile station_noshadow_20250824.csv -input_format noshadow
```

**Output**: Creates `station_noshadow_20250824_utm.csv`

**Command Line Arguments**:
- `-coords`: Comma-separated lat,lon coordinates
- `-ifile`: Input CSV file path
- `-input_format`: Format type (road_stretch or noshadow), default: road_stretch

**Dependencies**:
- `pyproj`: Coordinate transformation library
- `pandas`: CSV processing
- `numpy`: Array operations

**Notes**:
- Uses modern pyproj API (Transformer) compatible with Python 3.8+
- Old style using `Proj("+init=EPSG:...")` is commented out
- Output uses pipe delimiter (`|`) instead of comma
- No header row in output files
- Float precision: 3 decimal places (sufficient for meter-level accuracy)

**Error Handling**:
- Exits with error if unknown input format specified
- Validates command line arguments
- Requires either `-coords` or `-ifile` argument

---

### check_road_stations_dbase.py

**Purpose**: Validates station data against existing database to avoid reprocessing already-calculated stations.

**Location**: `scripts/check_road_stations_dbase.py`

**Description**:
This script checks if stations in the input CSV have already been processed by querying an SQLite database. It removes duplicate stations from the processing list and creates a backup of the original file.

**Key Features**:
- Database validation to prevent duplicate processing
- Automatic CSV file modification
- Backup creation of original files
- Support for both road and noshadow station formats
- SQLite and JSON database support

**Functions**:

#### `main(args)`
Main entry point that orchestrates the database checking process.

**Parameters**:
- `args.utm_list`: Path to CSV file with station coordinates
- `args.csv_id`: CSV identifier (not actively used)
- `args.out_dir`: Output directory
- `args.dbase_file`: Database file path

**Workflow**:
1. Reads station list from CSV
2. Checks against database
3. Removes already-processed stations
4. Exits if all stations already processed

#### `check_dbase(df_stretch, utmlist, dbfile)`
Checks road stations against SQLite database.

**Parameters**:
- `df_stretch`: DataFrame with station data
- `utmlist`: Path to UTM CSV file
- `dbfile`: SQLite database file path

**Database Schema**:
```sql
SELECT * FROM STATIONS
```

**Columns Used**:
- `station_id`: Station identifier

**Process**:
1. Connects to SQLite database
2. Reads all existing stations
3. Compares input stations with database
4. Removes duplicates from DataFrame
5. Rewrites CSV file without duplicates
6. Creates backup file with `.save` extension

**Output**:
- Modified CSV file (duplicates removed)
- Backup file: `original_file.csv.save`

#### `check_dbase_noshadows(df_stretch, utmlist, dbfile)`
Checks noshadow stations against JSON database.

**Parameters**:
- `df_stretch`: DataFrame with station data
- `utmlist`: Path to UTM CSV file
- `dbfile`: JSON database file path

**Database Format** (JSON):
```json
[
  "{\"station\": \"4031\", \"sensor\": \"0\"}",
  "{\"station\": \"4032\", \"sensor\": \"1\"}"
]
```

**Process**:
1. Loads JSON database
2. Parses JSON strings to dictionaries
3. Checks station + sensor combinations
4. Removes duplicates from DataFrame
5. Rewrites CSV file
6. Creates backup file

**CSV File Format**:

**Input (pipe-delimited)**:
```
easting|norting|station|sensor1|sensor2
567890.123|6234567.890|4031|0|0
567891.234|6234568.901|4032|1|0
```

**File Modification Process**:
1. Original file backed up to `filename.csv.save`
2. File read line by line
3. Lines with duplicate stations removed
4. Modified content written back to original filename

**Usage**:

```bash
python check_road_stations_dbase.py \
    -ul station_data_20250824_utm.csv \
    -cid 00 \
    -out /output/directory \
    -dbf shadows_data.db
```

**Command Line Arguments**:
- `-ul, --utm_list`: CSV file with stations in UTM coordinates (required)
- `-cid, --csv_id`: CSV file identifier (required)
- `-out, --out_dir`: Output directory (required)
- `-dbf, --dbase_file`: Database file path (required)

**Output Messages**:
```
Dropping station 5160 from input list, since it is already in database
Re-writing the list of stations station_data_20250824_utm.csv
Original list saved as station_data_20250824_utm.csv.save
```

**Exit Conditions**:
- Exits if database file doesn't exist (with warning)
- Exits if all stations already processed

**Dependencies**:
- `pandas`: DataFrame operations
- `sqlite3`: Database connectivity
- `json`: JSON database parsing (for noshadow)
- `search_zipfiles_nounzip.py`: TIF file utilities

**Use Cases**:
1. **Incremental Processing**: Only process new stations
2. **Crash Recovery**: Resume processing after failures
3. **Data Integrity**: Prevent duplicate entries in database
4. **Resource Optimization**: Avoid redundant calculations

**Notes**:
- Creates backup files automatically
- Modifies input CSV in place
- Supports both SQLite (road) and JSON (noshadow) databases
- Station comparison is case-sensitive

---

### search_zipfiles_nounzip.py

**Purpose**: Manages and locates DSM (Digital Surface Model) TIF files within compressed archives without extracting them.

**Location**: `scripts/search_zipfiles_nounzip.py`

**Description**:
This utility class provides efficient lookup of TIF files within zip archives. It maintains an index of zip file contents and can quickly determine which zip files contain specific TIF tiles needed for processing.

**Key Features**:
- Fast TIF file lookup without unzipping
- Zip file content indexing
- Disk space management
- Duplicate entry removal
- Processing history tracking

**Class: TIF_files**

#### `__init__(self, zipfiles, zipdir, outdir)`
Initializes the TIF file manager and builds the index.

**Parameters**:
- `zipfiles`: Path to file containing list of available zip files
- `zipdir`: Directory containing TIF file listings for each zip
- `outdir`: Output directory for extracted files

**Index Structure**:
```python
alltifs = {
    'DSM_DK_2020_01.zip': [
        'DSM_1km_6171_601.tif',
        'DSM_1km_6171_602.tif',
        ...
    ],
    'DSM_DK_2020_02.zip': [
        'DSM_1km_6172_601.tif',
        ...
    ]
}
```

**Initialization Process**:
1. Reads list of available zip files
2. For each zip file, reads corresponding TIF listing
3. Builds dictionary mapping zip files to their TIF contents
4. Stores in `self.alltifs` OrderedDict

**File Structure Expected**:
```
zipfiles: zip_files_list.txt
    DSM_DK_2020_01.zip
    DSM_DK_2020_02.zip
    ...

zipdir/: list_zip_contents/
    tif_files_DSM_DK_202.txt
    tif_files_DSM_DK_203.txt
    ...
```

#### `find_zipfiles(self, look_items)`
Finds which zip files contain the requested TIF files.

**Parameters**:
- `look_items`: List of TIF filenames to search for

**Returns**: Set of zip file names containing the requested TIFs

**Example**:
```python
tif_files = TIF_files(
    zipfiles='zip_files_list.txt',
    zipdir='list_zip_contents',
    outdir='/tmp/tifs'
)

needed_tifs = ['DSM_1km_6171_601.tif', 'DSM_1km_6171_602.tif']
zip_files = tif_files.find_zipfiles(needed_tifs)
# Returns: {'DSM_DK_2020_01.zip'}
```

**Algorithm**:
1. Iterate through each requested TIF file
2. Search all zip file contents for matches
3. Collect matching zip file names
4. Remove duplicates using set()
5. Return unique set of zip files

#### `check_storage(self)`
Monitors disk space usage and cleans up if necessary.

**Parameters**: None

**Returns**: Boolean indicating if cleanup was performed

**Configuration**:
- `maxsize`: 100,000 MB (100 GB) threshold

**Process**:
1. Checks current directory size using `du -sh`
2. If size exceeds threshold:
   - Deletes all `.tif` files in output directory
   - Returns `True` (cleaned)
3. If size under threshold:
   - No action taken
   - Returns `False` (not cleaned)

**Note**: Contains a typo in variable name (`checkzize` should be `checksize`)

**Main Script Usage**:

When run as a standalone script:

```bash
python search_zipfiles_nounzip.py "6171_601,6171_602" /tmp/tifs /data/DSM_DK
```

**Arguments**:
1. Comma-separated list of TIF block identifiers
2. Output directory for extraction
3. DSM data directory (optional, default: `/media/cap/7E95ED15444BBB52/Backup_Work/DMI/DATA_RoadProject/`)

**Workflow**:
1. Parses TIF block list
2. Constructs full TIF filenames: `DSM_1km_{block}.tif`
3. Finds required zip files
4. Checks storage space
5. Tracks processed zip files in `zipfiles_processed.txt`
6. Skips already-processed zip files

**Processing History**:
- File: `{outdir}/zipfiles_processed.txt`
- Contains list of already-extracted zip files
- Prevents redundant extraction
- Cleared if storage cleanup performed

**Example Processing History**:
```
DSM_DK_2020_01.zip
DSM_DK_2020_02.zip
DSM_DK_2020_03.zip
```

**HPC Integration**:
- `hpc_data = True`: Enables HPC data source
- Commented-out SCP commands for copying from HPC
- HPC path: `/data/cap/DSM_DK/`

**Dependencies**:
- `subprocess`: Shell command execution
- `pandas`: Not used in current implementation
- `collections.OrderedDict`: Ordered dictionary for zip file index

**Use Cases**:
1. **Efficient Lookup**: Find TIF files without extracting all archives
2. **Selective Extraction**: Only extract needed zip files
3. **Space Management**: Automatic cleanup when disk space low
4. **Processing Optimization**: Track already-processed files

**Limitations**:
- Extraction code is commented out (lines 109-114)
- Storage check has a typo in variable name
- Script exits before updating processing history (line 119)
- Primarily used as a library, not standalone script

**Integration**:
Used by `check_road_stations_dbase.py`:
```python
from search_zipfiles_nounzip import TIF_files as TIF_files
```

---

## Legacy Scripts

### daily_road_stations.sh

**Purpose**: Legacy script for processing road stations (superseded by parallel processing).

**Location**: `scripts/daily_road_stations.sh`

**Description**:
This is an older version of the daily processing script that handles only road stations with sequential processing and database checking. It has been largely replaced by `daily_processing_parallel.sh` but may still be used for specific scenarios.

**Key Features**:
- Sequential processing (non-parallel)
- Database validation to avoid reprocessing
- Simpler workflow than parallel version
- Fixed worker count (2 processors)

**Workflow**:

1. **Environment Setup**:
   - Activates Python environment
   - Sources environment configuration
   - Sets working directory variables

2. **Data Download**:
   - Executes `get_data.sh`
   - Creates `station_data_YYYYMMDD_utm.csv`
   - Validates CSV has data

3. **Database Validation**:
   - Checks stations against `shadows_data.db`
   - Removes already-processed stations
   - Exits if no new stations to process

4. **Processing**:
   - Runs with fixed 2 workers
   - Uses `--exit-on-grass-error` flag
   - Processes only road station type

**Command Executed**:
```bash
python /mnt/drive/hirtst/terrain-shadow-processor/src/run_parallel_processing.py \
    --csv $csv \
    --config /mnt/drive/hirtst/terrain-shadow-processor/config/shadows_conf.ini \
    --workers 2 \
    --output-dir /mnt/drive/hirtst/terrain-shadow-processor/data \
    --log-dir /mnt/drive/hirtst/terrain-shadow-processor/logs \
    --tiles-dir ${DSMPATH} \
    --work-dir /tmp/test_work \
    --type road \
    --exit-on-grass-error
```

**Differences from Parallel Version**:
- No noshadow station processing
- Fixed 2 workers (not configurable)
- Database checking before processing
- No post-processing or email notifications
- No cleanup of temporary files
- Simpler directory structure

**Exit Conditions**:
1. No data downloaded (CSV empty)
2. All stations already processed (after database check)

**Database Integration**:
```bash
DBASE="shadows_data.db"
python check_road_stations_dbase.py -ul $csv -cid 00 -out $WRKDIR -dbf $DBASE
```

**Use Cases**:
- Legacy compatibility
- Simple single-type processing
- Development and testing
- Scenarios where database validation is critical

**Status**: 
- **Deprecated**: Replaced by `daily_processing_parallel.sh`
- Kept for backward compatibility
- May be removed in future versions

---

## Environment Configuration

All scripts depend on `env.sh` which should define:

**Required Variables**:
- `PYBIN`: Python binary path
- `DSMPATH`: Path to DSM TIF files
- `WORKDIR`: Temporary working directory
- `OUTDIR`: Output directory for results
- `LOGDIR`: Log directory
- `GITREPO`: Path to git repository
- `NUM_WORKERS`: Number of parallel workers (default: 4)
- `BATCH_SIZE`: Batch size for processing

**Example env.sh**:
```bash
export PYBIN=/mnt/drive/hirtst/python-shadows/bin/python
export DSMPATH=/mnt/drive/hirtst/DSM_DK/tiles
export WORKDIR=/mnt/drive/hirtst/work
export OUTDIR=/mnt/drive/hirtst/output
export LOGDIR=/mnt/drive/hirtst/logs
export GITREPO=/mnt/drive/hirtst/terrain-shadow-processor
export NUM_WORKERS=4
export BATCH_SIZE=100
```

---

## Processing Pipeline Overview

### Complete Daily Workflow

```
1. loke_shadows_daily_crontab.sh (Cron Entry Point)
   └─> 2. daily_processing_parallel.sh (Main Orchestrator)
       ├─> 3a. get_data.sh (Download Road Stations)
       │   └─> calcUTM.py (Convert Coordinates)
       ├─> 3b. get_noshadow_stations.sh (Download Noshadow Stations)
       │   └─> calcUTM.py (Convert Coordinates)
       ├─> 4a. run_parallel_processing.py (Process Road Stations)
       ├─> 4b. run_parallel_processing.py (Process Noshadow Stations)
       └─> 5. Post-processing (Email Notifications)
```

### Manual Processing Workflow

```
1. run_single_date.sh YYYYMMDD [workers] (Manual Entry Point)
   └─> 2. run_parallel_processing.py (Process Specific Date)
```

### Testing Workflow

```
1a. test_small.sh (Quick Test)
    └─> run_parallel_processing.py (100 stations, 2 workers)

1b. test_long.sh (Extended Test)
    └─> run_parallel_processing.py (100k stations, 10 workers)
```

---

## File Formats

### Station CSV Format (Road Stations)

**Raw Download** (`station_data_YYYYMMDD.csv`):
```csv
5160,"Gjørup",9.36827374,56.65630341
5161,"Aalborg",9.92093658,57.04880905
```

**UTM Converted** (`station_data_YYYYMMDD_utm.csv`):
```
523456.789|6234567.890|5160|0|0
534567.890|6345678.901|5161|0|0
```

### Station CSV Format (Noshadow Stations)

**Raw Download** (`station_noshadow_YYYYMMDD.csv`):
```csv
4031,"Aarhus-Nord",0,0,0,10.111693,56.21921
4032,"Vejle",1,0,0,9.536789,55.709876
```

**UTM Converted** (`station_noshadow_YYYYMMDD_utm.csv`):
```
567890.123|6234567.890|4031|0|0
545678.901|6178901.234|4032|1|0
```

### Configuration File

**Location**: `config/shadows_conf.ini`

Contains GRASS GIS and processing parameters (see main documentation for details).

---

## Error Handling

### Common Error Scenarios

1. **Missing CSV File**:
   - Scripts check for file existence
   - Display available files for the date
   - Exit with descriptive error message

2. **Empty CSV File**:
   - Scripts validate file has content
   - Exit gracefully if no stations to process

3. **Download Failures**:
   - wget return codes checked
   - Error messages displayed
   - Processing halted

4. **Database Issues**:
   - Checks for database file existence
   - Warns if database missing
   - Exits to prevent data corruption

5. **GRASS GIS Errors**:
   - `--exit-on-grass-error` flag available
   - Errors logged to log directory
   - Processing can continue or halt based on flag

### Exit Codes

- `0`: Success
- `1`: Error (various causes)

### Logging

All scripts log to `${LOGDIR}` with timestamps and detailed progress information.

---

## Performance Considerations

### Worker Count Recommendations

- **Small datasets** (< 100 stations): 2-4 workers
- **Medium datasets** (100-1000 stations): 4-8 workers
- **Large datasets** (> 1000 stations): 8-16 workers

### Resource Usage

- **CPU**: Parallel workers utilize multiple cores
- **Memory**: Each worker requires ~2-4 GB RAM
- **Disk**: Temporary files can be large (cleanup performed)
- **Network**: Downloads from vejvejr.dk (minimal bandwidth)

### Optimization Tips

1. Use appropriate worker count for dataset size
2. Ensure sufficient disk space in `${WORKDIR}`
3. Use SSD for `${WORKDIR}` if possible
4. Monitor log files for bottlenecks
5. Consider database validation to avoid reprocessing

---

## Maintenance and Troubleshooting

### Regular Maintenance

1. **Log Rotation**: Regularly clean old logs from `${LOGDIR}`
2. **Disk Space**: Monitor `${WORKDIR}` and `${OUTDIR}` usage
3. **Database Backup**: Backup `shadows_data.db` regularly
4. **Cron Monitoring**: Check cron execution logs

### Troubleshooting Steps

1. **Check Logs**: Review logs in `${LOGDIR}`
2. **Verify Environment**: Ensure `env.sh` variables are correct
3. **Test Small Dataset**: Use `test_small.sh` to validate setup
4. **Check Permissions**: Verify write access to all directories
5. **Validate Data**: Ensure CSV files are properly formatted

### Common Issues

1. **Character Encoding**: Ensure iconv is available
2. **Python Environment**: Verify virtual environment activation
3. **GRASS GIS**: Check GRASS installation and configuration
4. **Network**: Verify connectivity to vejvejr.dk
5. **Disk Space**: Ensure sufficient space for processing

---

## Security Considerations

### Credentials

- vejvejr.dk credentials hardcoded in scripts
- Consider using environment variables or secure credential storage
- Credentials: `--user=vejvejr --password=settings`

### File Permissions

- Ensure proper permissions on output directories
- Protect database files from unauthorized access
- Secure log files containing processing details

### Network Security

- Downloads over HTTP (not HTTPS)
- Consider using HTTPS if available
- Validate downloaded data integrity

---

## Future Improvements

### Suggested Enhancements

1. **Configuration Management**:
   - Move hardcoded paths to configuration files
   - Centralize credential management
   - Support multiple environments (dev, prod)

2. **Error Handling**:
   - More granular error codes
   - Retry logic for network failures
   - Better error recovery mechanisms

3. **Monitoring**:
   - Add metrics collection
   - Performance monitoring
   - Alert system for failures

4. **Testing**:
   - Automated test suite
   - Continuous integration
   - Validation of output data

5. **Documentation**:
   - API documentation for Python modules
   - Deployment guide
   - Troubleshooting flowcharts

---

## Conclusion

The scripts in this directory form a comprehensive system for automated shadow calculation processing. The main production workflow is handled by `loke_shadows_daily_crontab.sh` and `daily_processing_parallel.sh`, with support for manual processing via `run_single_date.sh` and testing via `test_small.sh` and `test_long.sh`.
