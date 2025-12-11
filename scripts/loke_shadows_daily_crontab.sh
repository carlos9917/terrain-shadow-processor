#!/usr/bin/env bash
# Script to run both shadows and noshadows data on a crontab in loke

TODAY=`date '+%Y%m%d'`
#Processing both data sets for shadows
echo "Doing road stations"
./daily_road_stations.sh 
pid=$!
wait $pid
echo "Daily processing $pid finished"
echo "Doing new shadow data"
./daily_new_shadows.sh >& ./out_noshadows_call_${TODAY}

