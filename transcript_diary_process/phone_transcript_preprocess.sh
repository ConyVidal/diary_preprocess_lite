#!/bin/bash

# test using console and log file simultaneously
exec >  >(tee -ia transcript.log)
exec 2> >(tee -ia transcript.log >&2)

# this script handles all preprocessing/metadata organization/raw feature extraction on the transcript end for phone diaries.

# start by getting the absolute path to the directory this script is in, which will be the top level of the repo
# this way script will work even if the repo is downloaded to a new location, rather than relying on hard coded paths to where I put the repo. 
full_path=$(realpath $0)
#repo_root=$(dirname $full_path)
repo_root=/n/home_fasse/cvidal/ncf_user/diary_process_pipelines/transcript_diary_process
# export the path to the repo for scripts called by this script to also use - will unset at end
export repo_root

# gather user settings, first asking which study the code should run on - this is only setting currently for the viz side
#echo "Enter command in the formmat: bash script_name.sh study_name subject_id"
# NOTE: take command line argument as study name variable 
# E.g. bash phone_transcript_preprocess.sh FRESH_17 
study=$1
p=$2
export p
# NOTE: the location of the study
study_loc=/ncf/cnl03/PHOENIX/PROTECTED  
export study_loc 

# NOTE: the location of transcripts relative to each participant's directory
transcripts_loc=/phone/processed/audio/transcripts/transcript_data/
export transcripts_loc

model_path=$repo_root/NLP_models/GoogleNews-vectors-negative300.bin
export model_path


# sanity check that the study folder is real at least
cd $study_loc
if [[ ! -d $study ]]; then
	echo "invalid study id"
	exit
fi
cd "$study" # switch to study folder for first loop over patient list
# make study an environment variable, for calling bash scripts throughout this script. will be unset at end
export study


# let user know script is starting
echo ""
echo "Beginning script - phone transcript preprocessing for:"
echo "$study - $p"
echo ""


# add current time for runtime tracking purposes
now=$(date +"%T")
echo "Current time: ${now}"
echo ""

# convert the provided transcript txt files to CSV format for processing
echo "*************Converting newly pulled transcripts to CSV*************"
bash "$repo_root"/individual_modules/run_transcript_csv_conversion.sh
echo ""

# add current time for runtime tracking purposes
now=$(date +"%T")
echo "Current time: ${now}"
echo ""

# run transcript QC on all available transcripts for this study
echo "*************Running QC on all available transcripts for $p*************"
bash "$repo_root"/individual_modules/run_transcript_qc.sh
echo ""


# add current time for runtime tracking purposes
now=$(date +"%T")
echo "Current time: ${now}"
echo ""


# extract NLP features
echo "*************Extracting NLP features for all available transcripts*************"
bash "$repo_root"/individual_modules/run_transcript_nlp.sh
echo ""

# add current time for runtime tracking purposes
now=$(date +"%T")
echo "Current time: ${now}"
echo ""


# script wrap up - unset environment variables so doesn't mess with future scripts
unset study
unset repo_root
unset transcript_loc
unset model_path
unset patient
echo "=============Script completed============="

# add current time for runtime tracking purposes
now=$(date +"%T")
echo "Current time: ${now}"
echo ""

