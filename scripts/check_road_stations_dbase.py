'''
This module extends and integrates the calcTiles.py script

'''
import subprocess
import os
import pandas as pd
from datetime import datetime
import sys
import numpy as np
from collections import OrderedDict
from search_zipfiles_nounzip import TIF_files as TIF_files
import os
import shutil

def main(args):
    '''
    Works for any list of stations in a csv file.
    It will save results in directory stations_XX 
    '''
    utmlist=args.utm_list
    stnum=args.csv_id
    outdir=args.out_dir
    dbase_file = args.dbase_file

    stretchlist=pd.read_csv(utmlist,sep='|',header=None)
    stretchlist.columns=['easting','norting','station','sensor1','sensor2']
    #check if the data is already in the database and reduce it accordingly
    #Only do this if there is a database
    if os.path.isfile(dbase_file):
        check_stretch= check_dbase(stretchlist,utmlist,dbase_file)
        if check_stretch.empty:
            print("All data in %s already processed"%utmlist)
            print("Exiting")
            sys.exit()
    else:
        print("WARNING: No shadow database file present")
        sys.exit()

def check_dbase_noshadows(df_stretch,utmlist,dbfile):
    '''
    Check the new database
    '''
    #Dropping the sqlite dbase in favour of simple json
    #import sqlite3
    #con=sqlite3.connect(dbfile)
    #sql_command = "SELECT * FROM STATIONS"
    #data_old=pd.read_sql(sql_command, con)
    import json
    with open(dbfile,"r") as json_file:
        json_strings = json.load(json_file)
    old_dict=OrderedDict()
    for label in ["station","sensor"]:
        old_dict[label]=[]
    #json.load returns a list. Convert each element
    # of the list to dictionary with json.loads
    for json_str in json_strings:
        read_json = json.loads(json_str)
        old_dict["station"].append(int(read_json["station"])) #these are str by default
        old_dict["sensor"].append(int(read_json["sensor"]))
    data_old = pd.DataFrame(old_dict)
    df_temp=df_stretch.copy()#Remember you idiot, this is not a new var otherwise! 
    repeated=[]
    for k,station in enumerate(df_stretch['station']):
        sensor = df_stretch["sensor1"].values[k]
        check_row=data_old[(data_old['station']==station)
                          & (data_old['sensor']==sensor)]
        if not check_row.empty:
            print(f"Dropping {station}_{sensor} from input list, since it is already in database")
            repeated.append(str(station))
            df_temp.drop([k],inplace=True)

    #con.close()
    #This is just to save the original list. Probably not
    #necessary in the long run
    if len(repeated) != 0:
        new_lines=[]        
        print("Re-writing the list of stations %s"%utmlist)
        back_utm=utmlist+'.save'
        print("Original list saved as %s"%back_utm)
        cmd='cp '+utmlist+' '+back_utm
        ret=subprocess.check_output(cmd,shell=True)
        with open(utmlist,'r') as f:
            utm_orig=f.readlines()
        with open(utmlist,'w') as f:
            for line in utm_orig:
                station=line.split('|')[2]
                if station not in repeated:
                    f.write(line)
    return df_temp

def check_dbase(df_stretch,utmlist,dbfile):
    '''
    Check existing database and remove
    any existing data from df_stretch
    '''
    import sqlite3
    con=sqlite3.connect(dbfile)
    sql_command = "SELECT * FROM STATIONS"
    data_old=pd.read_sql(sql_command, con)
    df_temp=df_stretch
    repeated=[]
    for k,station in enumerate(df_stretch['station']):
        check_row=data_old[data_old['station_id']==station]
        if not check_row.empty:
            print("Dropping station %s from input list, since it is already in database"%station)
            repeated.append(str(station))
            df_temp.drop([k],inplace=True)

    con.close()
    #write the list of repeated stations
    #now=datetime.strftime(datetime.now(),'%Y%m%d_%H%M%S')
    if len(repeated) != 0:
        new_lines=[]        
        print("Re-writing the list of stations %s"%utmlist)
        back_utm=utmlist+'.save'
        print("Original list saved as %s"%back_utm)
        cmd='cp '+utmlist+' '+back_utm
        ret=subprocess.check_output(cmd,shell=True)
        with open(utmlist,'r') as f:
            utm_orig=f.readlines()
        with open(utmlist,'w') as f:
            for line in utm_orig:
                station=line.split('|')[2]
                if station not in repeated:
                    f.write(line)
    return df_temp

if __name__ == '__main__':
    import argparse
    from argparse import RawTextHelpFormatter

    parser = argparse.ArgumentParser(description='''If no argument provided it will take the default config file
             Example usage: python3 check_road_stations_dbase.py -ul $wrkdir/$csv -cid $st -out $wrkdir -td $scrdir''', formatter_class=RawTextHelpFormatter)

    parser.add_argument('-ul','--utm_list',
           metavar='the csv file with the stations in utm coordinates',
           type=str,
           default=None,
           required=True)

    parser.add_argument('-cid','--csv_id',
           metavar='the number of the csv file',
           type=str,
           default=None,
           required=True)

    parser.add_argument('-out','--out_dir',
           metavar='where to write the data',
           type=str,
           default=None,
           required=True)

    parser.add_argument('-dbf','--dbase_file',
           metavar='The sqlite file with the database',
           type=str,
           default=None,
           required=True)

    args = parser.parse_args()
    main(args)

