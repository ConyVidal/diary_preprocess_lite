# diary_preprocess_lite

This repository contains code and instructions to preprocess audio diaries collected as part of larger deep phenotyping studies in the Cognitive Neuroscience Laboratory at Harvard University (PI: Buckner). All code was adapted from [Michaela Ennis’ process_audio_diary repository](https://github.com/dptools/process_audio_diary) with help from Michaela Ennis and Jennie Li. 

Participants of the FRESH_17 and FRESH17_FOLLOWUP studies used the smartphone app Beiwe to record and submit daily voice diaries. These audio recordings are saved under the PROTECTED/phone/raw folder in the PHOENIX partition of ncf.

Quality control processing for voice diaries includes two main steps: audio file QC (main goal is to filter out unusable files before we send for transcription) and transcript QC (main goal is to ensure accuracy of the transcription). Each of these steps, in turn, includes manual and automated components. 

For the automated components, we adapted the dptools / process_audio_diary pipeline created and used in-house by members of the Baker Lab (main developer: Michaela Ennis) at McLean Hospital, which they use to QC their patients’ daily diaries as well as recorded therapy sessions. 

Our adapted diary_preprocess_lite repository is meant to be run in the FASSE cluster, and contains two sub-repositories: 
* minimal_audio_diary_process: This repo is a "light" version of the audio QC part of the original process_audio_diary pipeline, focusing on computing metrics of file length, mean volume, and flatness.
* transcript_diary_process: second, we adopted the transcript processing component of the pipeline, which includes the computation of both transcript QC metrics (e.g., number of sentences, number of speakers, number of inaudible marks) as well as implements some NLP algorithms for sentiment analysis (VADER), semantic coherence, and word commonness (through Google’s word2vec model).


---

### Table of Contents
1. [SETUP](#setup)
2. [AUDIO QC](#audio)
	- [Run automated audio QC pipeline](#autoaudio)
	- [Analyze automated audio QC metrics to identifying empty, invalid, and late diaries](#analyzeaudio)
	- [Transcript Processing Details](#transcript)
	- [Visualization Generation Details](#viz)
3. [TRANSCRIPT QC](#transcriptQC)
	- [Manual spot-checking and editing of subset of transcripts](#manualtrans)
	- [Run automated transcript QC pipeline](#autotrans)
	- [Analyze transcript QC pipeline outputs to identify potentially problematic transcripts](#analyzetrans)
	
### SETUP <a name="setup"></a>
For convenience, diary_preprocess_lite simply inherited the setup process from the original dptools / process_audio_diary pipeline (even though not all dependencies are necessary for this lite version of the pipeline). The setup instructions from the process_audio_diary pipeline are copied below, with a few tweaks to reflect idiosyncrasies of our cluster setup. Our diary_preprocess_lite repository includes a copy of the setup folder mentioned in the instructions below.

1. Connect to the RC VPN and open Terminal to ssh to fasse

2. Pull the diary_preprocess_lite repository to your local directory in FASSE (/n/home_fasse/username/). 

3. We will need miniconda and a few other packages to create the conda environment that contains all the dependencies for the pipeline to run smoothly. Load those packages by running the following three lines on Terminal:

    module load centos6/0.0.1-fasrc01
    module load ncf/1.0.0-fasrc01
    module load miniconda3/4.5.12-ncf


4. Create the Python conda environment ("audio_process") necessary to run this pipeline by moving to the setup folder and running:

    conda env create -f audio_process.yml


5. To activate the environment, which should be done each time before running the code, use:

    conda activate audio_process

Note that before the first time running on a new machine, it may be necessary to start Python (in the activated conda environment) and enter the following two commands, in order for the NLP features script to work:

    python
    import nltk
    nltk.download('cmudict')
    quit()

Similarly, a handful of the required packages are not conda installable, so that before the first the run the following should be entered on the command line (in the activated conda environment):

    pip install soundfile
    pip install librosa
    pip install vaderSentiment
    pip install wordcloud

If encounter the error "Could not install packages due to an OSError, Proxy URL had no scheme...", fix it by running:

    export http_proxy=http://rcproxy.rc.fas.harvard.edu:3128
    export https_proxy=http://rcproxy.rc.fas.harvard.edu:3128

It will also be necessary to install the lab encryption model for a first run, if the raw files need to be decrypted. To do so, enter the following command after activating the environment:

    pip install cryptease

Other dependencies are OpenSMILE (2.3.0) and ffmpeg (4.3.2), as well as the ability to run bash scripts and a working mail command - the latter two should be available on any standard Linux server.

After completing the setup instructions above, you should be ready to run the audio QC and transcript processing modules of the pipeline, described in detail below.


### AUDIO QC <a name="audio"></a>

We send audio diaries out to TranscribeMe for transcription. Before we do that, we complete audio QC. This first QC step focuses on the audio files themselves, as we want to filter out any untranscribable or otherwise unusable data so we don’t pay for those transcriptions unnecessarily. Unusable data includes empty files (participants would sometimes record a minute of no speaking just so they would get paid for submitting a file), multiple files submitted per day, and late submissions (our study’s cutoff for late submissions is anything past 6am the morning after the daily survey/diary opened).

After we receive transcripts back, there are additional steps for QC over the transcripts themselves (see "Transcript QC" section below).

Below I outline the steps I took to quality control all the available audio diaries we have from both the FRESH_17 and the FRESH17_FOLLOWUP studies. Since data collection had been finished by the time I started preprocessing the audio diaries, and since I had to decide what subjects’ data to prioritize for transcription among all available data given budget constraints, I performed the steps below sequentially for every single subject that provided audio diaries. Therefore, this part of the pipeline was already completed and should not be needed again for either of these two studies (FRESH_17 and FRESH17_FOLLOWUP). In contrast, I have been running the transcript_diary_processing side of the pipeline one subject at a time, each time I get transcript data from TranscribeMe.

The minimal_audio_diary_process module of the diary_preprocess_lite repository was run for each subject in both the FRESH_17 and FRESH17_FOLLOWUP studies. This lite version of the pipeline (adapted with help from Michaela Ennis) implements 3 main scripts in the original process_audio_diary pipeline, which work over a given subject’s audio files sequentially to complete the following three tasks:

**Step 1: Audio file decryption**

    + Script name: run_new_audio_decryption.sh
    + The script will proceed to decrypt all audio files (.wav.lock extension) in `/ncf/cnl03/PHOENIX/PROTECTED/FRESH_17/*subject*/phone/raw/*/voiceRecording/*` and place them in `/ncf/cnl03/PHOENIX/PROTECTED/*study*/*subject*/phone/processed/audio/temp_decrypted`. Terminal won’t show progress, but the user can refresh the folder on a separate terminal shell or in FASSEood to check it’s working. Once all files are decrypted for that subject, the user should check that they got the expected number of files decrypted (cross-check with the raw encrypted files). If everything looks good, we can proceed to producing metadata files (see below).

**Step 2: File renaming and metadata extraction**

    + Script name: run_audio_metadata.sh
    + First, it renames the audio files (from their original name which is just the submission timestamp in UTC time, per Beiwe’s default settings) to include study ID, subject ID, and file number (numbering is done based on all available files for that subject, ordered by submission timestamp). The files are kept in the same location.
    + Subsequently, it creates metadata files with original names of files, new name, and path to original file in PHOENIX. I use this path at a later step when adjusting for timezone. These files are saved in `/ncf/cnl03/PHOENIX/PROTECTED/*study*/*subject*/phone/processed/audio/FRESH_17_SUBJECT_phoneAudioDiary_fileMetadataMap.csv`.
    + Once the script is done, the user should check that they have the right number of files and that the file naming didn’t skip any numbers before proceeding to the next step.

**Step 3: Basic audio QC metrics computation**

    + Script name: run_audio_qc.sh
    + Computes basic QC stats on each audio file: length of file, acoustic volume, amplitude, etc., and compile them all into a CSV under `/ncf/cnl03/PHOENIX/PROTECTED/*study*/*subject*/phone/processed/audio/FRESH_17_SUBJECT_phoneAudioDiary_QC.csv`.


##### Run automated audio QC pipeline <a name="autoaudio"></a>

All scripts are to be run on the FASSE cluster using SLURM. If this is the first time using the diary_preprocess_lite pipeline, the user should first follow the setup instructions outlined above. Those setup instructions should only be needed the first time you use the pipeline. In subsequent uses, you just need to login to your FASSE account from Terminal, and navigate to the pipeline directory before you can run the script. Detailed instructions below: 

Connect to the VPN and ssh to your fasse account using Terminal
From Terminal, navigate to the ‘code’ folder inside the minimal_audio_diary_process. In my case: 

    cd ncf_user/diary_process_pipeline/diary_preprocess_lite/minimal_audio_diary_process/code)

The scripts will be run from this location in Terminal.

###### Sample code to run in FASSE

Note that the process to run these scripts is slightly different for FRESH_17 versus FOLLOWUP data, since the encryption/decryption mechanism is different and the data are located in different folders. Of note, you do *not* need to activate the conda environment before you run the script over the FRESH_17 data. You do need it when running over the FRESH17_FOLLOWUP data.

**CODE TO RUN IN FASSE FOR FRESH_17 DATA (for a sample subject)**

    module load ncf/1.0.0-fasrc01
    module load encrypt/0.6-ncf
    export ENCRYPT_PASS=[INSERT PASSCODE HERE]

Step 1: decryption 

    sbatch -p fasse --time 00:30:00 --mem 1G 
    run_new_audio_decryption.sh FRESH_17 voiceRecording 8TS58

Step 2: renaming and metadata

    sbatch -p fasse --time 00:05:00 --mem 1G 
    run_audio_metadata.sh FRESH_17 voiceRecording 8TS58

Step 3: audio QC metrics generation

Start new terminal and cd to ‘code’ folder of the pipeline

    cd ncf_user/diary_process_pipeline/diary_preprocess_lite/minimal_audio_diary_process/code
    module load centos6/0.0.1-fasrc01
    module load ncf/1.0.0-fasrc01
    module load miniconda3/4.5.12-ncf
    pip install --upgrade pip
    pip install soundfile
    conda deactivate
    conda activate audio_process

    sbatch -p fasse --time 00:30:00 --mem 1G   
    run_audio_qc.sh FRESH_17 8TS58


**CODE TO RUN IN FASSE FOR FRESH17_FOLLOWUP DATA (for a sample subject)**

    cd ncf_user/diary_process_pipeline/diary_preprocess_lite/minimal_audio_diary_process/code
    module load centos6/0.0.1-fasrc01
    module load ncf/1.0.0-fasrc01
    module load miniconda3/4.5.12-ncf
    pip install --upgrade pip
    pip install soundfile
    conda deactivate
    conda activate audio_process
    export ENCRYPT_PASS=[INSERT PASSCODE HERE]

Step 1: decryption

    sbatch -p fasse --time 00:30:00 --mem 1G 
    run_new_audio_decryption.sh FRESH17_FOLLOWUP 
    audio_recordings 2NB25

Step 2: renaming and metadata

    sbatch -p fasse --time 00:05:00 --mem 1G 
    run_audio_metadata.sh FRESH17_FOLLOWUP 
    audio_recordings 2NB25

Step 3: audio QC metrics generation

    sbatch -p fasse --time 00:30:00 --mem 1G 
    run_audio_qc.sh FRESH17_FOLLOWUP 2NB25

###### Checking scripts completed successfully
The sbatch command above will generate a slurm output report (saved in the folder where you ran the command in "slurm[JobID].out" format) that captures all messages printed to the console. 

Using "cat [report name], print the content of the report and make sure that there weren’t any warning or error messages and there are messages confirming that all scripts ran successfully. 

Run "sacct" to check if the slurm job is completed (sacct will show all recent processes submitted in the current session). 

After the job is completed with no warning messages, check memory usage using "seff [JobID]". 

Generally, the jobs take ~8 minutes altogether:
* Decryption: ~5 minutes
* File renaming and metadata generation:  <1 minute
* Audio QC metrics: ~2 minutes


##### Analyze automated audio QC metrics to identifying empty, invalid, and late diaries <a name="analyzeaudio"></a>

After running all the automated audio QC steps above, I downloaded all the generated csv files to my (encrypted) local computer and switched to R Studio to conduct QC checks on both the FRESH_17 and the FRESH17_FOLLOWUP diary data.

1. **In 1_DIARIES_identify_problematic_audio.R** I use the generated audio QC metrics to identify files with low volume, short duration, or multiple diary submissions in the same day. I manually listened to these "suspicious" files and moved them to a "DNU" folder (in my encrypted local computer) if the file was empty or otherwise invalid (e.g., subject had started speaking for a few seconds and then stopped and restarted in a new file— in this case, I only kept the second/full diary; subject recorded and submitted a diary twice because they thought it didn’t work the first time—in this case, I only kept the first/originally submitted file). Note that I might have missed some empty files this way, since sometimes subjects would record "empty" file (no speaking) with the TV on, so volume would sound comparable to other "valid" diaries.

2. **In 2_DIARIES_adjust_time_identify_usable.R**, for the files that passed the first step above, I use time zone data generated by Habib Rahimi-Eichi based on subjects’ GPS data (extracted from their phone) to adjust to local diary submission time. I label each file as late or on time. In this script I also generate csv files with usable/late data, both at diary level as well as subject summaries of how much usable data they have. I used these summaries to estimate the cost of transcription and decide on which subjects to prioritize given my budget. Subject-level files with adjusted timezone were uploaded to the cluster under `/ncf/cnl03/PHOENIX/PROTECTED/*study*/*subject*/phone/processed/audio/FRESH_17_SUBJECT_phoneAudioDiary_fileMetadata_timezoneCorrected.csv`

### TRANSCRIPT QC <a name="transcriptQC"></a>
Audio files that passed all QC metrics above were submitted to the TranscribeMe server for transcription. This process was done manually and one subject at a time. Each subject’s full usable data was submitted as a subfolder (titled with the subject ID) in the TranscribeMe server for easier handling (e.g., this way it’s easier to check the total number of files uploaded/expected/received). A running log of all audio file submissions and transcript deliveries is kept in transcript_QC_log.xls.

Once we get the transcripts back from TranscribeMe (this can take from a few business days to a few weeks), we run quality control checks over the transcriptions. This involves both manual and automated QC processing. 

##### Manual spot-checking and editing of subset of transcripts <a name="manualtrans"></a>

This step focuses on assessing the accuracy of the transcriptions received from TranscribeMe and identifying any corrections we want to ask of TranscribeMe. For instance, if we notice a repeated pattern of mistakes, we want to catch that early so we can ask them to correct it moving forward, before we send more data.

We asked TranscribeMe to send us all files for a given subject together in one batch (as opposed to sending a fraction of a subject’s files at a time, as they are transcribed). Usually they send one subject’s files at a time, and sometimes they send two full subjects at a time.

Upon receiving transcripts for a new subject (TranscribeMe sends an email notification when there are new transcripts available), check that you received transcripts for all audio files you submitted for that subject. 
* If some are missing, email TranscribeMe to let them know.

If all expected transcripts have been received, make two copies of the received transcripts:
1. Save a copy of the raw transcripts as downloaded from TranscribeMe server in (regularly backed-up) local computer. These will not be touched again.
2. Save a second copy of the transcripts in local computer, under study folder/data. These files will be edited as part of the spot-checking process described below, and will then be uploaded to the cluster.

*Spot-check* multiple transcripts (~30) for each subject, distributed across the study period (i.e., not just the first 30, but sampling in the beginning, middle, and end of study) against the original audio files and assess general accuracy. Mistakes to watch out for include:
* False "hits": Includes wrong words/sentences without any inaudible/questionable/redacted marks
* False "misses": Includes inaudible/questionable marks but you can actually tell what the participant is saying in the audio file
* Timestamp errors: You might notice two sentences have the same timestamp (this is rare, and should be picked up in automated QC, so no need to look too closely)

*Edit any discrepancies* noticed in those ~30 files, and keep record of these checks and edits in the transcript_QC.xls log (make a note under "General" tab to say you performed the checks, which files you checked, and then make more specific notes on what you edited under that subject’s tab).

After completing the spot-checking / editing process above:
1. **Upload all transcripts for the subject to PHOENIX**. These edited .txt files should be saved in `/ncf/cnl03/PHOENIX/PROTECTED/*study*/*subject*/phone/processed/audio/transcripts/transcript_data/`
2. **Delete the audio files from the TranscribeMe server (under the "audio" folder)**. I have been leaving the transcripts there as another backup.

For reference: Additional manual fixing/editing is done at later stages (during / post automated transcript QC):
* During automated transcript QC: Pipeline does not take any characters not in ASCII (you will get an error saying exactly which file and which sentence within it has the problem). These words need to be manually edited and the pipeline needs to be re-run for that participant.
* After automated transcript QC: The automated transcript QC pipeline generates transcript-level metrics for word count, volume, speaking rate, number of inaudible marks, etc. If any of these metrics looks out of the ordinary (e.g., an outlier number of inaudible marks that wasn’t caught in the first, spot-checking round, or implausibly fast speaking rate), we will go into that audio file and transcript and manually correct any mistakes caught. If any edits are made to the transcripts, the pipeline needs to be re-run for that participant.
* Later, during the manual coding process, if we ever encounter transcripts that don’t make sense (e.g. because there are too many inaudible marks), we will go back to the original audio file, see if we can tell what the participant is saying, and manually edit those files so we are then able to code them. Transcript QC pipelines **could** be run again after these edits, but it’s not really relevant/necessary at this point—the pipelines are meant to catch errors **before** the analysis stage.

##### Run automated transcript QC pipeline <a name="autotrans"></a>

We adapted the transcript QC pipeline developed by Michaela Ennis to process all transcript data we had in FRESH_17 and FRESH17_FOLLOWUP studies. The main script here is called phone_transcript_preprocess.sh. This script performs three sequential main steps, each by calling a different script in the background:

1. **run_transcript_csv_conversion.sh**: This script creates csv versions of all transcripts (originally in .txt format). The .txt files are in `/ncf/cnl03/PHOENIX/PROTECTED/*study*/*subject*/phone/processed/audio/transcripts/transcript_data`/, and the csv files are saved in `/ncf/cnl03/PHOENIX/PROTECTED/*study*/*subject*/phone/processed/audio/transcripts/transcript_data/csv/`
2. **run_transcript_qc.sh**: This script computes QC stats on each transcript (word count, number of sentences, number of inaudible, questionable, and redacted marks, quickest sentence) and compiles them all into a CSV per subject (each row is a transcript) under `/ncf/cnl03/PHOENIX/PROTECTED/*study*/*subject*/phone/processed/audio/transcripts/FRESH_17_SUBJECT_phoneAudioDiary_transcript_QC.csv`.
3. **run_transcript_nlp.sh**: This script computes automated NLP analyses per transcript, including speaking rate (syllables per second), sentiment analysis (using VADER algorithm), as well as word uncommonness and semantic coherence (using Google’s word2vec). I only focus on speaking rate and sentiment analysis outputs. These outputs are compiled in one CSV file per subject (each row is a transcript, each transcript is the mean across sentences in that file) under `/ncf/cnl03/PHOENIX/PROTECTED/*study*/*subject*/phone/processed/audio/transcripts/transcript_data/NLP_features/FRESH_17_SUBJECT_phoneAudioDiary_transcript_NLPFeaturesSummary.csv`. Transcript-level files are also created (each row is a sentence) and saved in `/ncf/cnl03/PHOENIX/PROTECTED/*study*/*subject*/phone/processed/audio/transcripts/transcript_data/NLP_features/csv_with_features`.

###### Implementation and sample code
I ran the phone_transcript_preprocess.sh script on the FASSE cluster. I had already followed the dptools / process_audio_diary setup instructions in Michaela’s pipeline’s GitHub repository to install all dependencies. Summer RA Jennie Li adapted Michaela’s transcript QC scripts under my supervision and followed my specific instructions according to the outputs I was interested in. We didn’t adapt every single step in the scripts, but rather only kept the steps we were interested in and that made sense for our data (described above). 

Jennie saved the updated scripts in her forked GitHub repository of Michaela’s pipeline (https://github.com/Jennie421/process_audio_diary). I downloaded and cleaned this repository (e.g., removed unused lines of code or unused sub-scripts, renamed folders to be more intuitive, etc.). I saved these scripts under a folder I named transcript_diary_process, in my local FASSE directory (cvidal/ncf_user/diary_process_pipelines/transcript_diary_process). I ran all transcript / NLP QC steps from there. 

We adapted the script to be runnable in batch through SLURM, as shown in the code below. Note that, by design, this command structure is the same for both studies: FRESH_17 and FRESH17_FOLLOWUP.

###### Setup steps (first-time users only)

1. Download the transcript_diary_process repository and save it in FASSE local directory (in my case: /n/home_fasse/cvidal/ncf_user/diary_process_pipelines/transcript_diary_process)
2. Downloading Google’s word2vec model and uploading to repository:
* Create a new folder inside the transcript_diary_process repo called NLP_models. 
Download google drive file with Google word2vec movel (https://drive.google.com/drive/u/0/folders/1CvMxoDiLmRhKoVQtzS4VXmQqN9iPAOJe) to local pc.
* Upload the model to the  minimal_transcript_QC/NLP_models subdirectory using the secure copy command: scp [local file] [username@fasselogin:~/foldername] 
In my case: /Users/conyvidal/Downloads/GoogleNews-vectors-negative300.bin.gz cvidal@fasselogin04:/n/home_fasse/cvidal/ncf_user/diary_process_pipelines/transcript_diary_process/NLP_models/
* From the minimal_transcript_QC/NLP_models directory, unzip the file using the command: gunzip GoogleNews-vectors-negative300.bin.gz
3. Edit any necessary paths to repository and to input/output data in the script phone_transcript_preprocess.sh. In our case:
* repo_root=/n/home_fasse/cvidal/ncf_user/diary_process_pipelines/transcript_diary_process
* study_loc=/ncf/cnl03/PHOENIX/PROTECTED 
* transcripts_loc=/phone/processed/audio/transcripts/transcript_data/
* model_path=$repo_root/NLP_models/GoogleNews-vectors-negative300.bin
4. Edit any other paths according to data location:
* Csv_with_features_path in run_transcript_nlp.sh. (In our case: `csv_with_features_path=$study_loc/"$study"/"$p"/phone/processed/audio/transcripts/NLP_features/csv_with_features`)
* audio_QC_path (audio QC output files) in phone_transcript_nlp.py (In our case: audio_QC_path = "../../../" + study + "_" + OLID + "_phoneAudioDiary_QC.csv")
5. The same dependencies and conda environment as in the Audio QC process are used for this pipeline. Make sure you follow the setup steps in Michaela’s pipeline (explained in Audio QC steps), including the creation of the conda environment audio_process, before running the code below.


###### Sample code to run in FASSE 

cd to folder with scripts and activate conda environment

    cd /n/home_fasse/cvidal/ncf_user/diary_process_pipelines/transcript_diary_process

    conda activate audio_process

command to run the script for a sample subject using SLURM

    sbatch -p fasse --time 00:30:00 --mem 6G   
    phone_transcript_preprocess.sh FRESH_17 7XP88

Note that both study name and subject ID should be specified in the command. The whole process takes about 6 minutes and a little over 4GB to run (6GB should be plenty).


###### Checking scripts completed successfully
The sbatch command above will generate a slurm output report (saved in the folder where you ran the command in "slurm[JobID].out" format) that captures all messages printed to the console. 

Using "cat [report name], print the content of the report and make sure that there weren’t any warning or error messages and there are messages confirming that all scripts ran successfully. There should be completion messages (including timestamps) for each of the three steps mentioned above (.txt to csv conversion of the transcripts, computation of transcript QC metrics, and NLP feature extraction).

Pay special attention at the beginning, during the .txt to .csv conversion, for any warning messages of issues with ASCII encoding. If any transcripts contain characters not in the ASCII system, the script will skip that file, not convert to csv, and therefore not include it in any subsequent processing. If there are any such instances:
1. Copy-paste those warning messages to this google doc.
2. Highlight the words that contain the problematic characters.
3. Manually fix those characters (e.g., remove accents) directly on the cluster’s .txt transcript files (not on csv folder)
4. Download the edited .txt files to the local computer and use to replace the former copies saved locally, so that all copies are up to date. 
5. Delete any output files that had already been generated during the transcript pipeline process for that subject (ie, csv folder with transcripts, transcript QC, NLP_features folder)
6. Re-run the pipeline and repeat all other steps above as needed.

Run "sacct"" to check if the slurm job is completed (sacct will show all recent processes submitted in the current session). 

After the job is completed with no warning messages, check memory usage using "seff [JobID]". 

Generally, the entire job takes ~6-7 minutes:
* Txt to csv: ~2.5 minutes
* Transcript QC:  <1 minute
* NLP feature extraction: ~4 minutes
