#!/usr/bin/env python

# prevent librosa from logging a warning every time it is imported
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)

# actual imports
import os
import pandas as pd
import numpy as np
import soundfile as sf
import librosa
import sys

def diary_qc(data_root, study, OLID, required_db=50):
	print("Computing new phone audio QC for patient " + OLID)
	# specify column headers that will be used for every CSV
	headers=["filename","length_minutes","num_channels","overall_db","amplitude_stdev","mean_flatness"]
	# initialize lists to fill in df
	fnames=[]
	lengths=[]
	ster_bools=[] # expect it to always be mono, but double check
	gains=[]
	stds=[]
	# spectral flatness is between 0 and 1, 1 being closer to white noise. it is calculated in short windows by the package used, so trying both mean and max summaries.
	mean_flats=[]

	try:
		os.chdir(os.path.join(data_root,"PHOENIX/PROTECTED",study,OLID,"phone/processed/audio/temp_decrypt"))
	except:
		print("Problem with input arguments, or haven't decrypted any audio files yet for this patient") # should never reach this error if calling via bash module
		return

	cur_files = os.listdir(".")
	cur_files.sort() # go in order, although can also always sort CSV later.
	if len(cur_files) == 0: # decrypted_audio folder may exist without any audio files in it when called from the feature extraction script, so add a check for that
		print("No new files for this patient, exiting") # should never reach this error if calling via bash module
		return
	for filename in cur_files:
		if not filename.endswith(".wav"): # skip any non-audio files (and folders)
			continue

		try:
			data, fs = sf.read(filename)
		except:
			# ignore bad audio - will want to log this for pipeline
			print(filename + " audio is broken, skipping")
			continue

		# get length info
		ns = data.shape[0]
		if ns == 0:
			# ignore empty audio - will want to log this for pipeline
			print(filename + " audio is empty, skipping")
			continue

		# add metadata info to lists for CSV
		fnames.append(filename) # this can be merged with the filemap CSV to get QC CSV with proper metadata

		# append length info
		sec = float(ns)/fs
		mins = sec/float(60)
		lengths.append(round(mins,2))

		try: # may not be a second shape number when file is mono
			cs = data.shape[1] # check number of channels
			if cs == 2: # if stereo calculate channel 2 properties, else append nans
				ster_bools.append(2)
				chan1 = data[:,0].flatten() # assume just chan 1 for now, but if anything shows up as stereo we may want to go back and add proper calculation of chan 2
			else:
				ster_bools.append(1)
				chan1 = data.flatten()
			vol = np.sqrt(np.mean(np.square(chan1)))
			gains.append(vol)
			stds.append(round(np.nanstd(chan1),5))
			spec_flat = librosa.feature.spectral_flatness(y=chan1)
			mean_flats.append(round(np.mean(spec_flat),5))
		except: # now it is definitely mono
			ster_bools.append(1)
			chan1 = data.flatten()
			vol = np.sqrt(np.mean(np.square(chan1)))
			gains.append(vol)
			stds.append(round(np.nanstd(chan1),5))
			spec_flat = librosa.feature.spectral_flatness(y=chan1)
			mean_flats.append(round(np.mean(spec_flat),5))

	# convert RMS to decibels
	ref_rms=float(2*(10**(-5)))
	db = [round(20 * np.log10(x/ref_rms), 3) for x in gains]

	# now prepare to save new CSV for this patient (or update existing CSV if there is one)
	os.chdir("..")

	# construct current CSV
	values = [fnames, lengths, ster_bools, db, stds, mean_flats]
	new_csv = pd.DataFrame()
	for i in range(len(headers)):
		h = headers[i]
		vals = values[i]
		new_csv[h] = vals

	# now save CSV
	output_path = study+"_"+OLID+"_phoneAudioDiary_QC.csv"
	new_csv.to_csv(output_path,index=False)

	try:
		prev_meta = pd.read_csv(study + "_" + OLID + "_phoneAudioDiary_fileMetadataMap.csv")
		prev_meta["filename"] = [x.split("/")[-1] for x in prev_meta["renamed_decrypted_file_path"].tolist()]
		combined_csv = new_csv.merge(prev_meta, on="filename", how="inner")
		combined_csv["subject_ID"] = [OLID for x in range(combined_csv.shape[0])]
		combined_csv = combined_csv[["subject_ID","recording_number","day","submission_hour","length_minutes","overall_db","amplitude_stdev","mean_flatness"]]
		combined_csv.to_csv(study+"_"+OLID+"_phoneAudioDiary_combinedMetadataAudioQC.csv",index=False)
	except:
		pass

	# now also move around files based on db cutoff - set default argument to require at least 40 db
	# could set the argument to None to turn it off
	if required_db is not None:
		os.chdir("temp_decrypt")
		try:
			os.mkdir("low_db")
		except:
			pass
		rejected_csv = new_csv[new_csv["overall_db"] <= required_db]
		files_to_move = rejected_csv["filename"].tolist()
		file_rename_args = [(x, "low_db/" + x) for x in files_to_move]
		for rej_f in file_rename_args:
			os.rename(rej_f[0], rej_f[1])

if __name__ == '__main__':
    # Map command line arguments to function arguments.
    diary_qc(sys.argv[1], sys.argv[2], sys.argv[3])
