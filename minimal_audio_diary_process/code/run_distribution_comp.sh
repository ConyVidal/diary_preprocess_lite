#!/bin/bash

data_root=/ncf/cnl03

echo "Study of interest?"
read study

echo "Absolute path to folder for combined distribution and histogram plot?"
read output_folder

python phone_diary_total_distributions.py "$data_root" "$study" "$output_folder"
