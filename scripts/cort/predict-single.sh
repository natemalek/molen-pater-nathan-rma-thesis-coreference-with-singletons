## this file is for debugging purpose

. output/cort/venv/bin/activate

output/cort/venv/bin/cort-predict-conll \
    -in data/conll-2012-flat/dev/bc_msnbc_0000.v4_auto_conll \
    -model models/cort/model-latent-train.obj \
    -out output/cort/dev_bc_msnbc_0000.v4_auto_conll.out \
    -extractor cort.coreference.approaches.mention_pairs.extract_testing_substructures \
    -perceptron cort.coreference.approaches.mention_pairs.MentionPairsPerceptron \
    -clusterer cort.coreference.clusterer.best_first

data/conll-2012/scorer/v8.01/scorer.pl all \
    output/cort/dev_bc_msnbc_0000.v4_auto_conll.out \
    data/conll-2012-flat/dev/bc_msnbc_0000.v4_auto_conll

deactivate