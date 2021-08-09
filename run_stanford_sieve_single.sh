#!/bin/bash
cd CoreNLP

JARS=`echo *.jar target/*.jar lib/*.jar | tr ' ' ':'`

java -Xmx6g -cp $JARS edu.stanford.nlp.dcoref.SieveCoreferenceSystem \
        -props sieve-english-conll.properties \
        -dcoref.all_gold True -dcoref.use_conll_auto $2 \
		-dcoref.conll2011 $1 \
        -dcoref.conll.output $3 \
        -dcoref.conll.scorer ../data/conll-2012/scorer/v8.01/scorer.pl
