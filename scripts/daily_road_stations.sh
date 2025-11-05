#!/bin/bash
# Process daily data for road stations
source /mnt/drive/hirtst/python-shadows/bin/activate
source /mnt/drive/hirtst/terrain-shadow-processor/env.sh


WRKDIR=$PWD
now=`date '+%Y%m%d_%H%M%S'`
today=`date '+%Y%m%d'`
cwd=$PWD

echo "--------------------------------------------"
echo "Daily station processing on $now"
echo "--------------------------------------------"

# Step 1.
#---------------------------------------------------------
# Run script to pullout station list from gimli server
#---------------------------------------------------------
./get_data.sh
csv=station_data_${today}_utm.csv
csv_len=$(wc -l $WRKDIR/$csv | awk '{print $1}')
echo "Length of $WRKDIR/$csv: $csv_len"
if [ $csv_len == 0 ]; then
   echo "No data downloaded for road stations"
   echo "File $csv is empty"
   echo "Stopping here"
   exit 0
fi

#the database with the road shadows. It will check if stations were already processed
DBASE="shadows_data.db"
python check_road_stations_dbase.py -ul $csv -cid 00 -out $WRKDIR -dbf $DBASE
#check list of stations again
csv_len=$(wc -l $WRKDIR/$csv | awk '{print $1}')
if [ $csv_len == 0 ]; then
  echo "All stations in $csv were processed alreay"
  echo "Stopping processing of road stations"
  exit 0
fi

NP=2 #number of processors to use

python /mnt/drive/hirtst/terrain-shadow-processor/src/run_parallel_processing.py \
    --csv $csv \
    --config /mnt/drive/hirtst/terrain-shadow-processor/config/shadows_conf.ini \
    --workers $NP \
    --output-dir /mnt/drive/hirtst/terrain-shadow-processor/data \
    --log-dir /mnt/drive/hirtst/terrain-shadow-processor/logs \
    --tiles-dir ${DSMPATH} \
    --work-dir /tmp/test_work \
    --type road \
    --exit-on-grass-error

