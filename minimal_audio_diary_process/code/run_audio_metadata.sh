#!/bin/bash

data_root=/ncf/cnl03

#echo "Study name?"
#read study
study="${1}"

#echo "Does Beiwe use audio_recordings or voiceRecording in the raw data paths for this study? Please type the name of the intermediate folder now"
#read raw_beiwe_name
raw_beiwe_name="${2}"

#echo "Patient ID to run on?"
#read patient
patient="${3}"

python phone_audio_metadata_format.py "$data_root" "$study" "$patient" "$raw_beiwe_name"
