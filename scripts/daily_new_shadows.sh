#!/bin/bash
# Process daily data for NEW road stations
source /mnt/drive/hirtst/python-shadows/bin/activate
source /mnt/drive/hirtst/terrain-shadow-processor/env.sh


WRKDIR=$PWD
now=`date '+%Y%m%d_%H%M%S'`
today=`date '+%Y%m%d'`
cwd=$PWD
RESDIR=./lh_500_0.4_11.25_00
SHADOWS=${RESDIR}_noshadows_${now} #this is where the data   will be stored

echo "--------------------------------------------"
echo "Daily station processing on $now"
echo "--------------------------------------------"

# Step 1.
#---------------------------------------------------------
# Run script to pullout station list from gimli server
#---------------------------------------------------------
./get_noshadow_stations.sh
csv=station_noshadow_${today}_utm.csv
if [ ! -f $csv ]; then
  echo "No $csv file generated. Stopping daily_new_shadows.sh script"
  exit 0
fi
csv_len=$(wc -l $WRKDIR/$csv | awk '{print $1}')
if [ $csv_len == 0 ];  then
  echo "No new stations to process today"
  exit 0
fi

# Run grass


NP=2 #number of processors to use

python /mnt/drive/hirtst/terrain-shadow-processor/src/run_parallel_processing.py \
    --csv $csv \
    --config /mnt/drive/hirtst/terrain-shadow-processor/config/shadows_conf.ini \
    --workers $NP \
    --output-dir /mnt/drive/hirtst/terrain-shadow-processor/data/$SHADOWS \
    --log-dir /mnt/drive/hirtst/terrain-shadow-processor/logs \
    --tiles-dir ${DSMPATH} \
    --work-dir /tmp/test_work \
    --type road \
    --exit-on-grass-error



# prepare data to be sent
NEWDATA=./deliver_station_data_${today}.txt
# this one runs in ./lh_500_0.4_11.25_00
# if directory is found, then generates the file NEWDATA
python ./prepare_message_newshadows.py -message $NEWDATA -shadows /mnt/drive/hirtst/terrain-shadow-processor/data/$SHADOWS

if [ -s $NEWDATA ]; then
 echo "New data available: $NEWDATA  --> Emailing data..."
 MESSAGE=email_${today}
 #Generate message
 cat message.txt $NEWDATA > $MESSAGE
 echo "message generated in $HOSTNAME" >> $MESSAGE
 python ./email_new_shadows.py $MESSAGE test_contacts.txt
fi

