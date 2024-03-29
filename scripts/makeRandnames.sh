#!/bin/bash

if [ $# -ne 2 ];
then echo -e "Not correct number of arguments specified. Usage:\nmakeRandnames.sh /tmp/infolder /tmp/outfolder";
  exit 1;
fi

INFOLDER=$1
OUTFOLDER=$2
#INFOLDER='../inputfiles/'
#OUTFOLDER='../outputfiles/'

mkdir -p "$OUTFOLDER"

cd "$(dirname "$0")"

#This file should take converted images and give them new randome names with the date to ensure we don't randomly fail to be random.
#It should also store a map file to get the orignal file names back.

currdate=$(date +"%Y%m%d")
outbase=$(basename "$OUTFOLDER")

#Get original file names
#Note, if you don't have the right pattern, this code will do nothing!
#Change pattern below if need be
filepattern="$INFOLDER*_red.tif"

filelist=$(ls $filepattern)

for file in $filelist:
do
   echo "Matched file: $file"
   filename=$(basename "$file")
   #echo $filename
   #strip file name to base
   origname=$(echo "$filename" | awk -F'_' '{print $1"_"$2"_"$3"_"}')

   echo "Stripped base name: $origname"
   #create new name
   newname=$(./genRand.sh)_$currdate
   echo "New name base: $newname"


   #write out translation file
   echo "$origname	$newname" >> "./mastertranslate_$outbase"

   #move the files that match to their new place
   #mv
   #use cp for testing
   currpattern=$INFOLDER$origname
   currfilelist=$(ls "$currpattern"*)
   echo "Matched files second:"
   echo "$currfilelist"
   for currfile in $currfilelist ;
   do
      echo "File to change name: $currfile"
      currnameonly=$(basename "$currfile")

      currnewnameonly=${currnameonly#$origname}
      currnewname=$OUTFOLDER$newname"_"$currnewnameonly
      echo "New name: $currnewname"
      cp "$currfile" "$currnewname"
   done


done
