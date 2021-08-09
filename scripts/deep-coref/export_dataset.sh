#!/bin/bash
# Convert a CoNLL dataset into a format that deep-coref can consume
# Usage: export_dataset.sh <input_dir> <output_dir>

set -x

cd CoreNLP
JARS=target/stanford-corenlp-3.7.0.jar:stanford-corenlp-models-current.jar:stanford-english-corenlp-models-current.jar:`echo lib/*.jar | tr ' ' ':'` && \

java -Xmx2g -cp $JARS edu.stanford.nlp.coref.neural.NeuralCorefDataExporter \
    -coref.flatInput $1 -coref.conll true \
    -coref.suffix _gold_conll -coref.md.useGoldMentions true \
    -coref.output $2 -coref.algorithm neural \