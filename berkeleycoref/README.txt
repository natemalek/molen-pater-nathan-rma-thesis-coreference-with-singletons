--------
Preamble
--------

The Berkeley Coreference Resolution System is a state-of-the-art English coreference
resolution system described in:

"Easy Victories and Uphill Battles in Coreference Resolution"
Greg Durrett and Dan Klein. EMNLP 2013.

This release also contains support for entity-level training and inference using
distributions over mention properties, as described in:

"Decentralized Entity-Level Modeling for Coreference Resolution"
Greg Durrett, David Hall, and Dan Klein. ACL 2013. 

You should generally cite the EMNLP paper unless you're actually using the
entity-level stuff.

See
http://www.eecs.berkeley.edu/~gdurrett/
for papers and BibTeX.

Questions? Bugs? Email me at
gdurrett@eecs.berkeley.edu

-------
License
-------

Copyright (c) 2013 Greg Durrett. All Rights Reserved.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

----------
Update Log
----------

2015-02-02: Version 1.1
--Randomizes the order of train documents by default, which leads to greatly improved
performance. Previously the behavior was nondeterministic.
--Can accept documents as input with nonconsecutive parts and filenames that do not
match the document names.

2013-11-11: Version 1.0
--Demonstrative pronouns are handled slightly differently in the featurization (helps slightly).
--Fixed a bug in the preprocessing where the last paragraph of raw text input would be dropped.
--Added better error handling and documentation for some common I/O problems.
--Now builds with the latest version of SBT

2013-11-03
--Now under the GPLv3

2013-10-29
--Now compiles under Scala 2.10.3 (was previously using the deprecated .first to get the first elements of Seqs)
--Bug fixes for running on raw text
--Included new pre-trained models that should perform better on raw text

2013-10-18
--Added pipeline support for running over raw text.

2013-09-19
--Preliminary version.

-----
Setup
-----

Coreference training and testing data:
Training and testing data are provided to the system as directories containing files ending in auto_conll or gold_conll
(usually the former, all experiments are done over auto annotation). These can be produced from the CoNLL shared task
data by flattening the directories as follows:

find . -path .*conll | while read file; do
  cp $file path/to/flattened/directory
done

Number and gender data: Available from:
http://old-site.clsp.jhu.edu/~sbergsma/Gender/index.html
Unzip to produce gender.data. The system expects this at data/gender.data, so if you put it here you won't have to think about it.
(Unfortunately, the system always tries to load it even if it won't be used...)

CoNLL scorer: Available from:
http://conll.cemantix.org/2012/software.html
There will be three things in the download: scorer.pl, CorScorer.pm, and a directory called Algorithm.
Put Algorithm and CorScorer.pl in the directory you run the jar from, or in lib/ under that directory. This way
they'll be located for scoring. scorer.pl can go anywhere as long as you pass in the appropriate path
with -conllEvalScriptPath

Note that all results in the paper come from version 5 of the CoNLL scorer. Other versions of the scorer may
return different results.

------------------------------
Running the coreference system
------------------------------

The main class is edu.berkeley.nlp.coref.Driver. You can run the system with:

java -jar -Xmx20g /path/to/jar ++base.conf \
  -execDir path-to-execution-directory \
  -trainPath path-to-ontonotes/train-flattened \
  -testPath path-to-ontonotes/test-flattened \
  -conllEvalScriptPath path-to-script/scorer.pl \
  -numberGenderData path-to-bergsma-lin/gender.data \
  -mode TRAIN_EVALUATE

The two other most important options are:
-modelPath (specify the file where the model should be read/written)
-outputPath (specify the file where predicted coreference output should be written. Note that this is a file, not a directory)

System modes:
TRAIN: Trains a model and writes it to modelPath.
  Requires: trainPath, modelPath
EVALUATE: On data with gold annotations, reads in a trained model and evaluates performance on that data using the CoNLL scorer.
  Requires: modelPath, testPath
PREDICT: On CoNLL-formatted data with no coreference information, reads in a trained model and writes to outputPath the same CoNLL data with predicted
  coreference clusters.
  Requires: modelPath, testPath, outputPath
TRAIN_EVALUATE, TRAIN_PREDICT: Trains a model and uses it for either EVALUATE or PREDICT as above. Model is not saved.
  Requires: trainPath, testPath
TWO_PASS: Runs TRAIN_EVALUATE, then prunes both training and testing data based on the trained model and retrains a new model
  with a new set of features and implements entity-level features as described in the ACL 2013.
  Requires: trainPath, testPath

Other options are discussed in edu.berkeley.nlp.coref.Driver. A few other useful ones:
-useGoldMentions
-trainOnGold (uses the gold_conll annotations)
-docSuffix (By default the system runs on auto CoNLL annotations. Change to gold_conll to run on gold annotations.)
-doConllPostprocessing (if false, allows you to keep singletons in output)
-numItrs (currently set to 20, can be set lower with only a small loss in performance to make the system train faster)

Pre-trained models over the CoNLL training set are included for both SURFACE and FINAL configurations.

Depending on how many documents you run on, the system may require 10-30GB of RAM to train (due to caching
feature vectors for every coreference arc). Prediction should be less intensive.

Features: These can be tweaked using -pairwiseFeats. Look in PairwiseIndexingFeaturizerJoint.scala for specific
feature options. Note that all of the "magic words" start with +, but the whole string cannot start with + or the
system will crash due to the vagaries of the option parsing code. Using -pairwiseFeats "FINAL" will use the FINAL features.

To reproduce SURFACE results on the CoNLL 2011 test set:
java -jar -Xmx30g /path/to/jar ++base.conf \
  -execDir path-to-execution-directory \
  -trainPath path-to-ontonotes/train-plus-dev-flattened \
  -testPath path-to-ontonotes/test-flattened \
  -conllEvalScriptPath path-to-script/scorer.pl \
  -numberGenderData path-to-bergsma-lin/gender.data \
  -mode TRAIN_EVALUATE

To run a pre-trained SURFACE model on the CoNLL 2011 dev set:
java -jar -Xmx30g /path/to/jar ++base.conf \
  -execDir path-to-execution-directory \
  -modelPath models/coref-surface.ser \
  -testPath path-to-ontonotes/test-flattened \
  -conllEvalScriptPath path-to-script/scorer.pl \
  -numberGenderData path-to-bergsma-lin/gender.data \
  -mode EVALUATE 

To reproduce FINAL results on the test set, add the appropriate -pairwiseFeats flag or use the pre-trained coref-trainplusdev-final model.

-------------
Preprocessing
-------------

The system is runnable from raw text as input. Pipeline stages:

Sentence-splitting: An unfaithful reimplementation of the method described in:
                    "Sentence Boundary Detection and the Problem with the U.S."
                    Dan Gillick. NAACL 2009.
                    Trained on the CoNLL newswire training data.

Tokenization: Penn Treebank tokenization.

Parsing: Uses the Berkeley Parser.

NER: Uses a custom NER system that's probably pretty bad, also it only spits out MISC tags.

To run this using the pretrained models, run:
java -cp /path/to/jar -Xmx10g edu.berkeley.nlp.coref.preprocess.PreprocessingDriver ++base.conf \
  -execDir path-to-execution-directory \
  -inputDir path/to/input-docs-directory-one-doc-per-file \
  -outputDir path/to/output-dir

If your data is already one sentence per line, add the -skipSentenceSplitting
flag. If it's split into paragraphs (i.e. some sentence boundaries are known),
use -respectInputLineBreaks (default: false) or -respectInputTwoLineBreaks
(default: true) to tell the system this, depending on whether paragraphs are
split by one new line or two.

Note that gzipped model files do not need to be unpacked before they can be
used by the system; the I/O knows how to handle .gz (the same goes when
producing models).

Look in edu.berkeley.nlp.coref.preprocess.NerDriver and
edu.berkeley.nlp.coref.preprocess.SentenceSplitterTokenizerDriver for how to
train new sentence splitting and NER models. New parser grammars can be trained
using the Berkeley Parser.

If you're running on raw text, you'll get better performance if you use
pretrained coref models trained on the CoNLL data annotated with the Berkeley
Parser and the custom NER system.  These are included in the models directory
as coref-rawtext-surface.ser and coref-rawtext-final.ser.

--------------------
Building from source
--------------------

The easiest way to build is with SBT:
https://github.com/harrah/xsbt/wiki/Getting-Started-Setup

then run

$ sbt assembly
which will compile everything and build a runnable jar.

You can also import it into Eclipse and use the Scala IDE plug-in for Eclipse
http://scala-ide.org

-------
  API
-------

Featurization is done in PairwiseIndexingFeaturizerJoint.featurizeIndex. This
adds the standard features (computed in featurizeIndexStandard). This is called
once for every mention pair, so it should be as optimized as possible. In
particular, properties specific to mentions should be cached in the Mention
objects if at all possible.

The easiest way to do this is to add accessors to Mention that implement a
cache (see Mention.cachedCanonicalPronConjStr for an example of this usage).
If you need properties that are computed with external tools, try adding them
to MentionPropertyComputer and then modfiying
Mention.createMentionComputeProperties.

------------
Known issues
------------

--If pairwiseFeats starts with +, the system will break due to how the options parsing works.
  --To resolve: add some character or word at the beginning; this won't change what features fire.
--Calling the scorer may cause an out-of-memory error because under the hood, Java
  forks the process and if you're running with a lot of memory, it will crash.
  --To resolve: run in PREDICT or TRAIN_PREDICT mode and manually call the scorer separately.

---------------
Troubleshooting
---------------

Common errors:

  0 docs loaded from 0 files, retaining 0
  ERROR: java.lang.UnsupportedOperationException: empty.reduceLeft:
  [...scala.collection calls...]
  edu.berkeley.nlp.coref.CorefDoc$.checkGoldMentionRecall(CorefDoc.scala:99)
  edu.berkeley.nlp.coref.CorefSystem$.loadCorefDocs(CorefSystem.scala:56)
  edu.berkeley.nlp.coref.CorefSystem$.runEvaluate(CorefSystem.scala:162)
  edu.berkeley.nlp.coref.CorefSystem$.runEvaluate(CorefSystem.scala:157)
  edu.berkeley.nlp.coref.CorefSystem.runEvaluate(CorefSystem.scala)
  edu.berkeley.nlp.coref.Driver.run(Driver.java:164)
  edu.berkeley.nlp.futile.fig.exec.Execution.runWithObjArray(Execution.java:479)
  edu.berkeley.nlp.futile.fig.exec.Execution.run(Execution.java:432)
  edu.berkeley.nlp.coref.Driver.main(Driver.java:156)

This means the system didn't load any documents. It expects files to end in auto_conll in
the given directories. If you want to run on gold_conll documents, use the -docSuffix flag
to change this.

