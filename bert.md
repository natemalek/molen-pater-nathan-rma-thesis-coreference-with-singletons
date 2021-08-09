# Steps to run experiments on BERT models.

**Notice! These steps are tested on Cartesius, you might need to adapt them to your environment.**

First, please download the repo and make sure Python3 is installed.

Run and mornitor the following step manually on an GPU-enabled environment:

    scripts/bert/setup.sh

This step can take hours to finish. Please make sure and everything is 
installed/downloaded/converted properly before proceeding.

    cd bert-coref
    . ../scripts/setup-cartesius.sh
    . ../output/bert/venv/bin/activate
    GPU=0 python train.py train_spanbert_base

At this point I got ["No such file or directory" error](https://github.com/mandarjoshi90/coref/issues/36) and 
some other errors when I tried to copy `bert_config.json` from a
pretrained model. Haven't figured out how to train the model yet.

You can start with running SpanBERT on the standard CoNLL-2012 data that
their script prepares. If you want to run on transformed corpora instead,
please prepare them in advance by putting OntoNotes 5.0 into folder 
`data/ontonotes-release-5.0` and running this command:

    drake output/e2e/conll-2012-resampled-minimized

The minimized datasets (`*.jsonlines`) will appear in the given folder,
in appropriate folder structure. You can train and run the model on any
of them.