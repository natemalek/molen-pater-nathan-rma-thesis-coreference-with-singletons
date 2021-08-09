# Usage: eval-single.sh <input_file>

cd CoreNLP

JARS=target/stanford-corenlp-3.7.0.jar:stanford-corenlp-models-current.jar:stanford-english-corenlp-models-current.jar:`echo lib/*.jar | tr ' ' ':'`

# you can set model path like this: -coref.neural.modelPath $2
java -Xmx6g -cp $JARS edu.stanford.nlp.coref.CorefSystem \
    -coref.algorithm neural \
    -coref.conll true -coref.suffix _gold_conll -coref.md.useGoldMentions true \
    -coref.inputPath $1  \
    -coref.conllOutputPath ../output \
    -coref.scorer ../reference-coreference-scorers/v8.01/scorer.pl
