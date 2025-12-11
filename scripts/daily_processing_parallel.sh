#!/bin/bash
# Parallel processing script for daily shadow calculations
# Refactored from daily_new_shadows.sh and daily_road_stations.sh

set -e  # Exit on error

# Set all paths and location of repo
source ../env.sh

# Use separate directories for different purposes
STATION_DATA_DIR=$PWD  # Where station CSVs are downloaded
now=$(date '+%Y%m%d_%H%M%S')
today=$(date '+%Y%m%d')
cwd=$PWD

# Create organized directory structure
mkdir -p ${WORKDIR}
mkdir -p ${OUTDIR}
mkdir -p ${LOGDIR}

echo "--------------------------------------------"
echo "Daily parallel station processing on $now"
echo "--------------------------------------------"

# Step 1: Download station data
#---------------------------------------------------------
echo "Downloading station data..."

# Process road stations
if [ -f ./get_data.sh ]; then
    ./get_data.sh
    csv_road=station_data_${today}_utm.csv
else
    echo "Warning: get_data.sh not found"
    csv_road=""
fi

# Process noshadow stations
if [ -f ./get_noshadow_stations.sh ]; then
    ./get_noshadow_stations.sh
    csv_noshadow=station_noshadow_${today}_utm.csv
else
    echo "Warning: get_noshadow_stations.sh not found"
    csv_noshadow=""
fi

# Step 2: Check if we have data to process
#---------------------------------------------------------
has_road_data=false
has_noshadow_data=false

if [ -n "$csv_road" ] && [ -f "$csv_road" ]; then
    csv_len=$(wc -l $csv_road | awk '{print $1}')
    if [ $csv_len -gt 0 ]; then
        echo "Found $csv_len road stations to process"
        has_road_data=true
    fi
fi

if [ -n "$csv_noshadow" ] && [ -f "$csv_noshadow" ]; then
    csv_len=$(wc -l $csv_noshadow | awk '{print $1}')
    if [ $csv_len -gt 0 ]; then
        echo "Found $csv_len noshadow stations to process"
        has_noshadow_data=true
    fi
fi

if [ "$has_road_data" = false ] && [ "$has_noshadow_data" = false ]; then
    echo "No stations to process today"
    exit 0
fi

# Step 3: Set up GRASS directories in working directory (not mixed with data)
#---------------------------------------------------------
[ ! -d ${WORKDIR}/grassdata ] && mkdir -p ${WORKDIR}/grassdata
[ ! -d $HOME/.grass7 ] && mkdir -p $HOME/.grass7

if [ -d $GITREPO/config/RoadStations ]; then
    cp -r $GITREPO/config/RoadStations ${WORKDIR}/grassdata/ 2>/dev/null || true
fi
if [ -d $GITREPO/config/rc_files ]; then
    cp $GITREPO/config/rc_files/rc* $HOME/.grass7 2>/dev/null || true
fi

# Step 4: Run parallel processing
#---------------------------------------------------------
echo "Starting parallel processing..."

# Process road stations in parallel
if [ "$has_road_data" = true ]; then
    echo "Processing road stations in parallel..."
    echo "  Input CSV: ${STATION_DATA_DIR}/${csv_road}"
    echo "  TIF files: ${DSMPATH}"
    echo "  Output: ${OUTDIR}/road_${today}"
    echo "  Logs: ${LOGDIR}"

    $PYBIN $GITREPO/src/run_parallel_processing.py \
        --csv ${STATION_DATA_DIR}/${csv_road} \
        --config $GITREPO/config/shadows_conf.ini \
        --workers ${NUM_WORKERS:-4} \
        --output-dir ${OUTDIR}/road_${today} \
        --log-dir ${LOGDIR} \
        --tiles-dir ${DSMPATH} \
        --work-dir ${WORKDIR}/road_${today} \
        --type road
fi

# Process noshadow stations in parallel
if [ "$has_noshadow_data" = true ]; then
    echo "Processing noshadow stations in parallel..."
    echo "  Input CSV: ${STATION_DATA_DIR}/${csv_noshadow}"
    echo "  TIF files: ${DSMPATH}"
    echo "  Output: ${OUTDIR}/noshadow_${today}"
    echo "  Logs: ${LOGDIR}"

    $PYBIN $GITREPO/src/run_parallel_processing.py \
        --csv ${STATION_DATA_DIR}/${csv_noshadow} \
        --config $GITREPO/config/shadows_conf.ini \
        --workers ${NUM_WORKERS:-4} \
        --output-dir ${OUTDIR}/noshadow_${today} \
        --log-dir ${LOGDIR} \
        --tiles-dir ${DSMPATH} \
        --work-dir ${WORKDIR}/noshadow_${today} \
        --type noshadow
fi

echo "Parallel processing completed"

# Step 5: Post-processing and notifications
#---------------------------------------------------------
echo "Post-processing results..."

if [ "$has_noshadow_data" = true ]; then
    # Prepare message for noshadow stations
    NEWDATA=${OUTDIR}/deliver_station_data_${today}.txt
    if [ -f ${STATION_DATA_DIR}/prepare_message_newshadows.py ]; then
        python ${STATION_DATA_DIR}/prepare_message_newshadows.py \
            -message $NEWDATA \
            -shadows ${OUTDIR}/noshadow_${today}

        if [ -s $NEWDATA ]; then
            echo "New data available: $NEWDATA  --> Emailing data..."
            MESSAGE=${OUTDIR}/email_${today}

            if [ -f $GITREPO/email_scripts/message.txt ]; then
                cat $GITREPO/email_scripts/message.txt $NEWDATA > $MESSAGE
            else
                cat $NEWDATA > $MESSAGE
            fi

            echo "message generated on $HOSTNAME at $(date)" >> $MESSAGE

            if [ -f ${STATION_DATA_DIR}/email_new_shadows.py ]; then
                python ${STATION_DATA_DIR}/email_new_shadows.py \
                    $MESSAGE \
                    $GITREPO/email_scripts/contacts.txt
            fi
        fi
    fi
fi

# Cleanup temporary working directories
echo "Cleaning up temporary files..."
rm -rf ${WORKDIR}/road_${today}
rm -rf ${WORKDIR}/noshadow_${today}
rm -f ${WORKDIR}/grass_calls*.out

echo ""
echo "Results saved to:"
[ "$has_road_data" = true ] && echo "  Road stations: ${OUTDIR}/road_${today}"
[ "$has_noshadow_data" = true ] && echo "  Noshadow stations: ${OUTDIR}/noshadow_${today}"
echo "Logs saved to: ${LOGDIR}"

echo "--------------------------------------------"
echo "Daily processing completed successfully"
echo "--------------------------------------------"
