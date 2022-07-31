#!/bin/bash

data_root=/ncf/cnl03

#echo "Study name?"
#read study
study="${1}"

#echo "Patient ID to run on?"
#read patient
patient="${2}"

python phone_audio_qc.py "$data_root" "$study" "$patient"
