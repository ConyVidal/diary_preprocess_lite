# set of functions for generating visualizations

import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
plt.ioff()
import matplotlib.backends.backend_pdf
import matplotlib.cm as cm
import pandas as pd
import numpy as np

# creates a pdf where each page is a histogram for one feature's distribution from an input distribution dataframe (specified as path to a CSV)
# all columns of the input CSV will be included as a page, unless added in the optional ignore_list argument. column names will be used as title of respective pages
# if a list of bin numbers is provided, then that list will be used in column order to specify the number of bins in the histogram
# similarly for ranges, which are expected to be provided if bin numbers are
# pdf is saved to the provided output path, nothing is returned
def distribution_plots(dist_df, pdf_save_path, ignore_list=[], bins_list=None, ranges_list=None, xlabel="Value", ylabel="Counts"):
	pdf = matplotlib.backends.backend_pdf.PdfPages(pdf_save_path)
	if bins_list is not None:
		count = 0
		if ranges_list is None:
			print("please provide a min and max along with a number of bins")
			return
	for col in dist_df.columns:
		if col in ignore_list:
			continue
		cur_dist = dist_df[col]
		fig = plt.figure(1)
		if bins_list is not None:
			plt.hist(cur_dist.dropna(),bins=bins_list[count],range=ranges_list[count])
			count = count + 1
		else:
			plt.hist(cur_dist.dropna())
		plt.title(col)
		plt.xlabel(xlabel)
		plt.ylabel(ylabel)
		plt.axis('tight')
		plt.tight_layout()
		pdf.savefig(fig,bbox_inches="tight")
		plt.close()
	pdf.close()
	return