#!/bin/bash
# Get data from website, update database
# 
# If arg 1 not given it will generate one from server
# If arg 1 is given it will only convert lat/lon to UTM coordinates

source /mnt/drive/hirtst/python-shadows/bin/activate
source /mnt/drive/hirtst/terrain-shadow-processor/env.sh


today=`date +'%Y%m%d'`
if [ -z $1 ]; then
  CSV=station_data_$today.csv
    echo "Downloading data from vejvejr.dk"
    wget -O out.tmp --user=vejvejr --password=settings "http://vejvejr.dk/glatinfoservice/GlatInfoServlet?command=stationlist"
    #Get rid of those annoying danish characters...
    cat out.tmp | iconv -f iso8859-1 -t utf-8  > $CSV
    rm -f out.tmp
else
  CSV=$1
  echo "File provided by user: $CSV. Doing only lat/lon to UTM conversion"
fi

#convert to UTM
echo Converting coordinates to UTM
python ./calcUTM.py -ifile station_data_$today.csv 
