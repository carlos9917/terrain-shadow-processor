from collections import OrderedDict
import os,sys
import subprocess

class TIF_files:
    def __init__(self,zipfiles,zipdir,outdir):
        #Read the available data and setup the dicts
        self.zipfiles=zipfiles #'zip_files_list.txt'
        self.zipdir=zipdir #'list_zip_contents'
        self.outdir=outdir
        zipList=[]
        with open(zipfiles) as f: 
            for line in f: 
                zipList.append(line.rstrip())
        alltifs=OrderedDict()
        for key in zipList:
            fname=os.path.join(zipdir,'tif_files_'+key[0:10]+'.txt')
            tiflist=[]
            with open(fname) as f:
                for line in f:
                    tiflist.append(line.rstrip())
            alltifs[key] = tiflist
        self.alltifs = alltifs
        self.tiflist = tiflist

    def find_zipfiles(self,look_items): #tiflist):
        #find the zip files I need to uncompress
        #according to the tiflist
        found_keys=[]
        for look_item in look_items:
            for zipfile in self.alltifs.keys():
                if look_item in self.alltifs[zipfile]:
                    #print("Found it %s"%zipfile)
                    found_keys.append(zipfile)
        #remove any repeated entries
        found_keys=set(found_keys)
        return found_keys            

    def check_storage(self):
        '''
        Determine if I am using too much disk space.
        If so, delete some files before continuing
        '''
        maxsize=100000 # in MB
        checksize=int(subprocess.check_output(['du','-sh', path]).split()[0].decode('utf-8').replace('M',''))
        if checksize > maxsize:
            print("Cleaning the directory %s before continuing (size=%d)"%(self.outdir,checksize))
            for tfile in os.listdir(self.outdir):
                if tfile.endswith(".tif"):
                    print("Deleting file %s"%os.path.join(self.outdir,tfile))
                    os.remove(os.path.join(self.outdir,tfile))
            cleaned=True        
        else:
            print("Directory size still under the limit (%d). No cleaning done"%checkzize)
            cleaned=False
        return cleaned
if __name__ == '__main__':
    hpc_data = True # If true, scp the zip file from hpc directory
    input_tiffiles=sys.argv[1] # the tif files I need to unzip
    outdir=sys.argv[2] #the directory where to extract their contents
    keeptrackfile=os.path.join(outdir,'zipfiles_processed.txt') # file to keep track of what I already unzipped
    #optional parameter
    try: 
        dsmdir=sys.argv[3]
    except IndexError:    
        #set the default location
        dsmdir='/media/cap/7E95ED15444BBB52/Backup_Work/DMI/DATA_RoadProject/'
    #print("dsmdir set as %s"%dsmdir)

    tifblocklist=input_tiffiles.split(",")
    look_items=[]
    for item in tifblocklist:
        look_items.append(''.join(['DSM_1km_',item,'.tif']))
    #cdir=os.getcwd()
    cdir='/data/cap/DSM_DK/SCRIPTS/CalculateTiles'
    avail_tifs=TIF_files(zipfiles=os.path.join(cdir,'zip_files_list.txt'),zipdir=os.path.join(cdir,'list_zip_contents'),outdir=outdir)
    zipfiles=avail_tifs.find_zipfiles(look_items)
    #print("Need to uncompress these files")
    #print(zipfiles)
    #check storage, delete data if needed
    cleaned=avail_tifs.check_storage
    if cleaned==True:
        #delete file with list of all uncompressed zip files if it is there
        exists=os.path.isfile(keeptrackfile)
        if exists==True:
            os.remove(keeptrackfile)
        zipsdone=[]    
    else:    
        exists=os.path.isfile(keeptrackfile)
        if exists==True:
            with open(keeptrackfile) as f: 
                zipsdone = [line.rstrip() for line in f.readlines()]
        else:
            zipsdone=[]

    for zfile in zipfiles:
        thisfile=os.path.join(dsmdir,zfile)
        if zfile in zipsdone:
            print("%s already unzipped"%zfile)
        else:    
            #hpc: get file via scp first!
            if hpc_data:
                hpcfile=os.path.join('/data/cap/DSM_DK/',zfile)
                #print("Copying file from hpc: %s"%hpcfile)
                #cmd='scp freyja-2.dmi.dk:'+hpcfile+' '+thisfile
                #out=subprocess.check_output(cmd,stderr=subprocess.STDOUT,shell=True)
            #print("Unzipping %s"%zfile)
            print(zfile)
            #cmd='unzip '+thisfile+' -d '+outdir
            #out=subprocess.check_output(cmd,stderr=subprocess.STDOUT,shell=True)
            #for tifblock in tifblocklist:
            #    thistif='DSM_1km_'+tifblock+'.tif'
            #    cmd='unzip '+thisfile+' '+thistif+' -d '+outdir
            #    out=subprocess.check_output(cmd,stderr=subprocess.STDOUT,shell=True)
            zipsdone.append(zfile)
            
    #print("zip files done")
    #print(zipsdone)
    sys.exit()
    #update the file with new contents
    exists=os.path.isfile(keeptrackfile)
    if exists==True:
        os.remove(keeptrackfile) #delete old file if already there
    print("(Re-)Creating file with list of unzipped files")    
    with open(keeptrackfile,'w') as f:
        for item in zipsdone:
            f.write('%s\n'%item)
        #check which files are now there, keep track of this
        #for tfile in os.listdir(outdir):
        #    if tfile.endswith('.tif'):
        #        tiffilesdone.append(tfile)
    #import pdb
    #pdb.set_trace()
