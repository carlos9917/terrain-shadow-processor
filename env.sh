# Environment configuration for parallel shadow calculations
# Source this file before running the processing scripts

# Location of the refactored git repo
export GITREPO=/mnt/drive/hirtst/terrain-shadow-processor

# Location of the source scripts
export SCRDIR=/mnt/drive/hirtst/terrain-shadow-processor/src

# Local path for DSM tiles (separate from working directory to avoid mixing TIF files with outputs)
# Option 1: Keep TIF files where they are (messy but existing)
export DSMPATH=/mnt/drive/hirtst/DSM_DK/
# Option 2: Move TIF files to dedicated directory (recommended)
# export DSMPATH=/mnt/drive/hirtst/DSM_tiles/

# -----------------------------
# GRASS GIS Configuration
# -----------------------------
# GRASS project location (will be created per batch)
export GRASSPROJECT=/mnt/drive/hirtst/terrain-shadow-processor/local_processing/grassdata/mytemploc_dk

# GRASS project settings template
export GRASSPROJECTSETTINGS=/mnt/drive/hirtst/terrain-shadow-processor/config/RoadStations

# The GRASS binary
export GRASSBINARY=/usr/bin/grass78

# The Python binary (from virtual environment)
export PYBIN=/mnt/drive/hirtst/python-shadows/bin/python

# -----------------------------
# Parallel Processing Settings
# -----------------------------
# Number of parallel workers (0 = auto-detect CPU count - 1)
export NUM_WORKERS=4

# Maximum batch size (stations per worker)
export BATCH_SIZE=100

# Working directory for temporary files (separate from TIF files and outputs)
export WORKDIR=/mnt/drive/hirtst/shadow_processing/work

# Output directory base (separate from working and TIF directories)
export OUTDIR=/mnt/drive/hirtst/shadow_processing/output

# Log directory
export LOGDIR=/mnt/drive/hirtst/terrain-shadow-processor/logs
