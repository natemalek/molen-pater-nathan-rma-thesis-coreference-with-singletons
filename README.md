

This repository contains experiments for the paper "An Input Ablation Analysis of Coreference Resolution Systems", and the follow-up work for the thesis "Information Usage in Coreference Resolution". The original respository for the former can be found here: https://bitbucket.org/cltl/even/src/master/.

The additions and alterations to the original repository are summarized here:
- added scripts/singletons/, containing code to add singletons to the OntoNotes data.
- some files, including consolidate_corpora.py and mask_mentions_or_context.py, were copied from their original location to the main directory for ease of usage. Others were altered slightly.
- This repository is designed to work with the Ontonotes 4.0 dataset; the original was built for Ontonotes 5.0.

Using this repository:
 - The original work, for "An Input Ablation Analysis of Coreference Resolution Systems", is bound in the Drakefile (which has not been altered). See below for more information on that. The commands in this drakefile will work with the present repository.
 - The additional work (the data manipulation) is not contained in the Drakefile. This manipulation (adding singletons) is done after the Drakefile data processing steps, using the file gen_singleton_files.py (see this file's docstring for more information).


Additional useful info: 

# Code structure

Most of what the code does is to train and evaluate models developed elsewhere, with the exception of
baselines and data transformation operations. A [Drakefile](https://github.com/Factual/drake)
(similar to Makefile but for data) is used to bind everything together.
Some models are included with slight changes (e.g. `deep-coref`, `e2e-coref`) but you probably won't need to look into them. These are the type of files to look into:

- Baseline implementation: `baselines.py`
- Manipulation implementation: `manipulations*.py`
- Notebooks for data preparation and reporting: `notebooks/`
- Scripts to handle data and models: `scripts/`
- Workflow specification: `Drakefile-vu` and `scripts/run-steps-on-cartesius*.{sh,job}`

# Set up

Make sure Python3, Maven, and [drake](https://github.com/Factual/drake) is installed.

Install software packages:

    pip3 install --user -r requirements.txt
    cd CoreNLP
    mvn clean package

If you run experiments on a Mac, you might need to install coreutils:

    brew install coreutils

## e2e-coref

I found this step to be very sensitive to hardware and environment
settings. I got a version that works on the Dutch Cartesius system, but can't guarantee
that it works for you:

    scripts/e2e/setup.job

## Stanford deep-coref

Setup `deep-coref`:

    scripts/deep-coref/setup.sh

I also used this script to install a missing dependency on my cluster: `scripts/deep-coref/setup-das5.sh`.

# Download data and models

Download OntoNotes 5.0 and put into folder `data/ontonotes-release-5.0`

## For experiments with cort

Download pretrained `cort` models:

    scripts/cort/download_models.sh

## For experiments with Stanford neural net models

Download English models (see instructions in [Stanford CoreNLP website](http://stanfordnlp.github.io/CoreNLP/coref.html#running-on-conll-2012)) and put into `CoreNLP`:

- `stanford-corenlp-models-current.jar`
- `stanford-english-corenlp-models-current.jar`
- `stanford-english-kbp-corenlp-models-current.jar`

# Reproduce results

**Notice! Many scripts are sensitive to environmental settings, I have tried to capture them as much as possible but please expect to fix missing packages and version mismatches etc.**

## Setting up experimental environment

Study the file `scripts/setup-cartesius.sh` (for most experiments) 
and `scripts/deep-coref/setup-cartesius-conda.sh` (for `deep-coref`).
Setup your environment accordingly.

## Setting up reporting environment

I used this sequence to setup my environment:

    conda create -n EvEn python=3.6 anaconda
    conda activate EvEn
    CFLAGS=-stdlib=libc++ pip install jpype1
    pip install -r requirements.txt
    conda install nb_conda=2.2.1
    python -m ipykernel install --name conda-env-EvEn-py


## Running experiments

Copy file `Drakefile-vu` to `Drakefile`. Some commands might not work on your system so you
might want to adapt that file when things break. It is ignored by git so it won't be affected
when you check out revisions.

I used the following sequence of commands to obtain the results on the Dutch DAS-5 cluster. 
Again, commands might not work on your environment, please study the scripts and adapt them
accordingly.

    sbatch scripts/run-steps-on-cartesius1.job # CPU
    # wait until the job finishes
    scripts/run-steps-on-cartesius2.sh # start a bunch of GPU jobs
    # wait until all jobs finish
    scripts/run-steps-on-cartesius2b.sh # some more jobs that depend on the previous ones
    # wait until all jobs finish
    sbatch scripts/run-steps-on-cartesius3.job # CPU again
