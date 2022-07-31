#!/bin/bash

code_dir=$(pwd)
export PATH=$code_dir:$PATH
chmod +x "$code_dir"/crypt_exp

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

#echo "Decryption passphrase?"
#read -s password
#password="concavity reverie nonstick strategy"

cd "$data_root"/PHOENIX/PROTECTED/"$study"/"$patient"

# create processed audio output folder under phone
mkdir phone/processed/audio
# create temporary folder for the decrypted files
mkdir phone/processed/audio/temp_decrypt

# some files are under additional subfolder - repeat similar process
for file in phone/raw/*/"$raw_beiwe_name"/*/*.wav.lock; do
	# get metadata info
	nameint=$(echo "$file" | awk -F '/' '{print $6}')
	name=$(echo "$nameint" | awk -F '.' '{print $1}')
	date=$(echo "$name" | awk -F ' ' '{print $1}')
	time=$(echo "$name" | awk -F ' ' '{print $2}')
	hour=$(echo "$time" | awk -F '_' '{print $1}')

	if [[ -e phone/processed/audio/temp_decrypt/"$date"+"$time".wav ]]; then
		# don't redecrypt if already decrypted for this batch!
		continue
	fi

	# now decrypt
	#crypt_exp "$password" phone/processed/audio/temp_decrypt/"$date"+"$time".wav "$file" > /dev/null
	crypt.py --decrypt --output-file phone/processed/audio/temp_decrypt/"$date"+"$time".wav "$file" > /dev/null
done
