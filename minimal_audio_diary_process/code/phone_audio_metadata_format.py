#!/usr/bin/env python

import pandas as pd
import numpy as np
import math
import os
import sys
from datetime import date, timedelta, datetime
import pytz

# https://stackoverflow.com/questions/2881025/python-daylight-savings-time -> I do assume he is always in eastern time! could eventuall work in gps for travel accounting but not worth it now. I dont think he travels a lot anyway
def is_dst(dt, timezone="US/Eastern"):
    timezone = pytz.timezone(timezone)
    timezone_aware_date = timezone.localize(dt, is_dst=None)
    return timezone_aware_date.tzinfo._dst.seconds != 0

def create_eastern_time_filemap(data_root, study, OLID, raw_beiwe_name, hour_offset=6):
	try:
		study_metadata = pd.read_csv(os.path.join(data_root, "PHOENIX/GENERAL", study, study + "_metadata.csv"))
		patient_metadata = study_metadata[study_metadata["Subject ID"] == OLID]
		consent_date_str = patient_metadata["Consent"].tolist()[0]
		consent_date = datetime.strptime(consent_date_str,"%Y-%m-%d")
	except:
		print("No consent date found for subject in study metadata, exiting")
		return

	try:
		os.chdir(os.path.join(data_root, "PHOENIX/PROTECTED", study, OLID, "phone/raw"))
	except:
		# either patient has no phone data, or something is wrong with the input - just exit if so
		print("No raw phone diary data exists for input arguments, exiting") # provide info on why function exited, in case called from outside pipeline
		return

	folders=os.listdir(".")
	files = []
	files_absolute = []
	for folder in folders:
		try: # some phones have no audio recording at all! prevent script from crashing though in case another phone does have some files
			files_test = os.listdir(os.path.join(folder,raw_beiwe_name))
		except:
			continue
		files_true = [x for x in files_test if x.endswith(".lock")]
		files.extend(files_true)
		files_true_absolute = [os.path.join(folder,raw_beiwe_name,x) for x in files_true]
		files_absolute.extend(files_true_absolute)
		# this does assume that anything not ending in .lock is a folder, but that historically holds true for Beiwe audio, shouldn't be a problem
		subfolders_true = [x for x in files_test if not x.endswith(".lock")] 
		for subfolder in subfolders_true:
			files_sub = os.listdir(os.path.join(folder,raw_beiwe_name,subfolder))
			files.extend(files_sub)
			files_sub_absolute = [os.path.join(folder,raw_beiwe_name,subfolder,x) for x in files_sub]
			files_absolute.extend(files_sub_absolute) 
	if len(files) == 0:
		print("No raw phone diary data exists for input arguments, exiting") # provide info on why function exited, in case called from outside pipeline
		return
	indices_sorted = sorted(range(len(files)), key=lambda k: files[k])
	file_paths_final = [files_absolute[i] for i in indices_sorted]

	df_columns = ["recording_number", "assigned_date", "submission_hour", "day", "raw_file_path", "renamed_decrypted_file_path"]
	recording_number = []
	assigned_date = []
	submission_hour = []
	study_day = []
	raw_path = []
	final_decrypt_path = []
	
	oneday=timedelta(days=1)
	cur_recording_number = 1
	for f in range(len(file_paths_final)):
		file_real = file_paths_final[f]
		file = file_paths_final[f].split("/")[-1] # remove the absolute path info for following part
		try:
			name = file.split(".")[0]
			date_str = name.split(" ")[0]
			year = int(date_str.split("-")[0])
			month = int(date_str.split("-")[1])
			day = int(date_str.split("-")[2])
			time = name.split(" ")[1]
			hour = int(time.split("_")[0])
			try: 
				dst_bool = is_dst(datetime(year=year,month=month,day=day,hour=hour))
				# this part is conversion from UTC to ET
				if dst_bool:
					hour = hour - 4
				else:
					hour = hour - 5
			except:
				hour = hour - 4
			# if answers prior to 6 am (per default argument), count it as previous day! -> hours will range from 6 to 29 instead of 0 to 23
			hour_date = hour - hour_offset 
			date_form = date(year,month,day)
			if hour_date < 0:
				hour = hour + 24
				true_date = date_form - oneday
				date_str = true_date.isoformat()	
		except:
			print("Name formatted incorrectly for: " + file + ", ignoring") # even for pipeline purposes will want to know if a file is found in raw not matching expected naming conventions
			cur_recording_number = cur_recording_number + 1
			continue

		first_file_rename = file.split(" ")[0] + "+" + file.split(" ")[1]
		first_file_rename = first_file_rename.split(".")[0] + ".wav"
		this_date = datetime.strptime(date_str,"%Y-%m-%d")
		day_num = (this_date - consent_date).days + 1
		final_file_rename = study + "_" + OLID + "_phoneAudioDiary_recording" + str(cur_recording_number).zfill(4) + ".wav"
		full_decrypt_path = os.path.join(data_root, "PHOENIX/PROTECTED", study, OLID, "phone/processed/audio/temp_decrypt", first_file_rename)
		full_decrypt_path_rename = os.path.join(data_root, "PHOENIX/PROTECTED", study, OLID, "phone/processed/audio/temp_decrypt", final_file_rename)

		os.rename(full_decrypt_path, full_decrypt_path_rename)

		recording_number.append(cur_recording_number)
		assigned_date.append(date_str)
		submission_hour.append(hour)
		study_day.append(day_num)
		raw_path.append(os.path.join(data_root, "PHOENIX/PROTECTED", study, OLID, "phone/raw", file_real))
		final_decrypt_path.append(full_decrypt_path_rename)

		cur_recording_number = cur_recording_number + 1

	df_vals = [recording_number, assigned_date, submission_hour, study_day, raw_path, final_decrypt_path]

	map_csv = pd.DataFrame()
	for i in range(len(df_columns)):
		label = df_columns[i]
		value = df_vals[i]
		map_csv[label] = value
	map_csv.to_csv(os.path.join(data_root, "PHOENIX/PROTECTED", study, OLID, "phone/processed/audio", study + "_" + OLID + "_phoneAudioDiary_fileMetadataMap.csv"), index=False)

if __name__ == '__main__':
    # Map command line arguments to function arguments.
    create_eastern_time_filemap(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
