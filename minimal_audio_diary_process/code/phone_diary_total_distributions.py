#!/usr/bin/env python

import os
import pandas as pd
import sys
import glob
from viz_helper_functions import distribution_plots

# make study-wide distribution plots for audio QC from phone diaries
def study_dists(data_root, study, output_folder):
	dist_path = os.path.join(output_folder, study + "-phoneAudioQC-distribution.csv")
	pdf_path = os.path.join(output_folder, study + "-phoneAudioQC-distributionHistograms.pdf")

	dist_df = pd.DataFrame()

	all_combined_paths = os.path.join(data_root, "PHOENIX/PROTECTED", study, "*", "phone/processed/audio", study + "*" + "phoneAudioDiary_combinedMetadataAudioQC.csv")
	path_list = glob.glob(all_combined_paths)

	# load each df to concatenate
	for csv in path_list:
		cur_dist = pd.read_csv(csv)

		if dist_df.empty:
			dist_df = cur_dist
		else:
			dist_df = pd.concat([dist_df, cur_dist], ignore_index=True, sort=False) # add sort = False to prevent future warning
			dist_df.reset_index(drop=True, inplace=True)

	# now save the new study-wide dist
	dist_df.to_csv(dist_path, index=False)

	distribution_plots(dist_df, pdf_path, ignore_list=["subject_ID","recording_number","day"])

if __name__ == '__main__':
    # Map command line arguments to function arguments.
    study_dists(sys.argv[1], sys.argv[2], sys.argv[3])
