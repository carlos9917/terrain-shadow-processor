"""
Look at the data generated (if any) and format it in specified format: 
station_number,sensor_number,shadow_1....shadow_32

Save in file to be emailed later.

Update data in json file.

Example output:
1549,0,0,10,6,4,4,4,6,4,2,8,6,2,2,0,0,0,0,0,0,0,0,0,0,0,0,0,2,4,2,0,0,0
2038,0,6,6,4,4,2,2,2,0,2,6,13,15,19,21,22,22,22,22,17,15,11,6,0,0,0,2,2,4,4,6,6,6

Direction is clock wise.
  0 North
 90 east
180 south
270 West

All shadow angles are rounded to the nearest integer.

Routines:
---------
standardToCompass(angle: `float`)
   convert angle measured from +X angle to meteorological standard

"""

import pandas as pd
import os
import numpy as np
import sys

def standardToCompass(angle):
    """
    Convert angle measured from +X axis counterclockwise
    to angle measured clockwise from +Y axis
    This only works for *wind directions*!
    Parameters
    ----------
    angle: `float`
           The angle to convert
    Yields
    ------
    `float`
           The angle converted to meteorological convention

    Examples:
    >>> standardToCompass(13.4)

    """
    compass = 90 - angle
    if compass < 0:
        compass = compass + 360
    compass = compass + 180
    if compass >= 360:
        compass = compass - 360
    #Up to here the result is ok for wind fetch,
    # but I want just the angle
    compass = compass + 180    
    #reset to 0 if it goes above 360
    if compass >= 360:
        compass = compass - 360
    return compass

def reformat(datapath) -> None:
    """
    Reformat the data to be sent
    """
    stations = []
    for ifile in sorted(os.listdir(datapath)):
        fpath=os.path.join(datapath,ifile)
        if ifile.startswith("lh_") and os.path.getsize(fpath) > 0:#will probably find shadows.log here
            station = ifile.split("_")[1]
            sensor = ifile.split("_")[2]
            data = pd.read_csv(fpath)
            angles = data.azimuth.to_list()
            shadows = data.horizon_height.to_list()
            angles_rot=[]
            for angle in angles:
                convAngle = standardToCompass(angle)
                #print(f"converting angle {angle} to {convAngle}")
                angles_rot.append(convAngle)
            s = np.array(angles_rot)
            sort_index = np.argsort(s)
            clean_shadows = []
            #replace the neg values with 0, and round horizon angle
            # to nearest integer
            for shadow in shadows:
                if shadow < 0:
                    clean_shadows.append(0)
                else:    
                    clean_shadows.append(round(shadow))
            shadows_order = [str(clean_shadows[i]) for i in sort_index]
            angles_order = [angles_rot[i] for i in sort_index]
            print("Ordered angles and shadows")
            print_df = pd.DataFrame({"angle":angles,
                                     "shadow": shadows, 
                                     "angle_rotated": angles_rot,
                                     "angle_met": angles_order,
                                     "shadow_met": shadows_order})
            print(print_df.to_markdown())
            stations.append(",".join([station,sensor]+shadows_order))
            stations.append("\n")
        elif os.path.getsize(fpath) == 0:
            print(f"{fpath} is empty!")
    return stations     

def export_email_message(stations,fout,user="cap") -> None:
    """
    Save the email to be sent. Not using the mail command
    from volta, since it does not work
    """
    import subprocess
    txt = "".join(stations)
    with open(fout,"w") as f:
        f.write(txt)

    #cmd='mail -s "Shadows data" '+user+'@dmi.dk < '+ fout
    #print(cmd)
    #try:
    #    out=subprocess.check_output(cmd,stderr=subprocess.STDOUT,shell=True)
    #except subprocess.CalledProcessError as err:
    #    print("Email failed with error %s"%err)


def save2json(input_filename,output_filename):
    """
    Save the station data in json format
    The input_filename is the one to be emailed

    """
    import json
    all_data=[]
    #open the old file if already there
    if os.path.isfile(output_filename):
        print("Data file already there. Checking contents")
        with open(output_filename,"r") as json_file:
            json_strings = json.load(json_file)
        for json_str in json_strings:
            read_json = json.loads(json_str)
            station = read_json["station"]
            sensor = read_json["sensor"]
            print(f"Station and sensor: {station} {sensor}")
            all_data.append(json_str)
    print(f"Currently read {len(all_data)}")
    with open(input_filename,"r") as f:
        lines=f.readlines()
        station_dict={}
        for line in lines:
            station_dict["station"] = line.split(",")[0]
            station_dict["sensor"] = line.split(",")[1]
            station_dict["data"] = data=",".join(line.rstrip().split(",")[2:])
            #convert dict to json
            y=json.dumps(station_dict)
            all_data.append(y)
    all_data=sorted(set(all_data)) #select only not repeated
    print("Strings to write")
    print(len(all_data))
    with open(output_filename,"w") as f:
        json.dump(all_data,f,indent=4)


if __name__=="__main__":
    import argparse
    from argparse import RawTextHelpFormatter
    parser = argparse.ArgumentParser(description='''
             Example usage: python3 ./prepare_message_newshadows.py -shadows ./lh_500_0.4_11.25_00 -message deliver_data.txt''', formatter_class=RawTextHelpFormatter)

    parser.add_argument('-shadows',
           help='The directory where the shadows are stored',
           type=str,
           default='./lh_500_0.4_11.25_00',
           required=False)

    parser.add_argument('-message',
           help='The name of the file with the message to email',
           type=str,
           default=None,
           required=True)

    parser.add_argument('-dbase',
           help='The name of file with the json data',
           type=str,
           default="./data_noshadows.json",
           required=False)

    args = parser.parse_args()

    datapath = args.shadows
    if not os.path.isdir(datapath):
        print(f"{datapath} does not exist!")
        sys.exit(1)
    file2email = args.message #"deliver_station_data.txt"
    file2json = args.dbase
    #Read data in output dir and reformat for email
    stations = reformat(datapath)
    #Export the message to be emailed later
    export_email_message(stations,file2email)
    #Save the data to json file
    save2json(file2email,file2json)

