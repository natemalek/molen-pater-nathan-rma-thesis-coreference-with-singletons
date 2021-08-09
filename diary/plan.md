
## March 2018

- [x] Feature list as comprehensive as possible
- [x] Draft a paper: motivations, main contributions, sections
- [x] Describe Textual Component Ablation Analysis
- [x] Implement new transformations
- [x] Remove roles of masked tokens
- [x] Write a better introduction section based on Antske's comment: a way to 
experimentally explore and get new ideas...
- [x] Describe detailed experimental settings
- [x] List the most popular names in CoNLL-2012

## April 2018
- [x] make same names in different documents the same or different
- [x] Run two coref systems against transformed corpora 
- [x] Finalize a list of systems to evaluate

## June 2018
- [x] Create flattened datasets out of datasets in `output/conll-2012-manipulated2.2018-04-13-271bf1e/`
- [x] Find out how to run e2e on custom input (see `experiments.conf` and `train.english.v4_auto_conll`)

## July 2018
- [x] Find out how to make e2e use gold mention spans
- [x] Find out how to run cort on custom input

## August 2018
- [x] Train e2e for a short time on each dataset
- [x] Train `e2e` on all manipulated corpora for 1hr (using `gpu-short` partition)
- [x] !IMPORTANT! Define baselines and run them on transformed corpora
- [x] Evaluate result of `e2e`

## September 2018
- [x] Rerun manipulations (because I forgot to include original datasets) and consolidation
- [x] Figure out how to train `cort`
- [x] Rerun Stanford sieve
- [x] Extract results of Stanford sieve
- [x] Rerun baselines
- [x] Rerun baseline results extraction script
- [x] Extract mention identification precision/recall too so that it's easier to check that we are using gold mention spans
- [x] Use gold mention spans for both gold and auto mention spans, retrain for gold instead of auto mention spans
- [x] Test `drake`

## October 2018
- [x] Send MTurk task to CLTL, improve based on feedback
- [x] Add monitoring code (record all events in the form, with timestamps, to the input called #events)
- [x] Cookies
- [x] Changed name-masked tasks so that people can work with them more easily
- [x] Fixed an error that prevent test auto_conll files from being generated
- [x] Do the expert pilot HITs by myself

## Nov 2018
- [x] Add "submit at top" link to the task
- [x] Write Piek and Antske about aggregation
- [x] Try to train `cort` on all manipulated corpora on loan laptop
- [x] Submit new Cartesius application
- [x] Figured out how to use HTML/JS without Kyoto

## Jan 2019
- [x] require people to finish one sentence before continue with the next, add check afterwards to detect if people select arbitrarily, tell people that you monitor things
- [x] Try to annotate few manipulated documents by myself
- [x] ask for confirmation when people want to combine two big groups
- [x] fix captured space/enter problem
- [x] fix the wrong mention count in submission message
- [x] warn when people leave the page
- [x] stabalize color assignment and give sensible precedence of one chain 
over the other while merging
- [ ] presentation: goals, guide, tricks
- [ ] measure on colleagues (speed, quality) and project to student assistant --> how much data we could get done, make plan on 28 Jan and have a meeting with Piek the week after
- [ ] allow moving between blanks by hitting the spacebar
- [ ] Test task on real annotators with, e.g., 5 documents

- [ ] Evaluate Cort-EM against transformed corpora
- [ ] Evaluate Cort-MP against transformed corpora
- [ ] Evaluate Cort-MR against transformed corpora

- [ ] what needs to be done for the paper?

- [ ] Run `cort` on all data
- [ ] Retrain `deep-coref` (see `scripts/train-deep_coref.job`)
- [ ] Generate chunk-based questions from manipulated corpora  
- [ ] Check the performance (F1) of MTurk workers
- [ ] Fix this issue with cort: https://github.com/smartschat/cort/issues/23
- [ ] Check correctness, if ok, train e2e for 2 days for each dataset
- [ ] Evaluate Berkeley against transformed corpora
- [ ] Pilot: what is the optimal way to gather annotations?

## Backlog

- [ ] Write discussions
- [ ] Write conclusion
- [ ] Annotation: deploy on Amazon MTurk
- [ ] Gather and analyze results
- [ ] When running `cort` with gold mention spans, we got 100% precision but lower recall,
find out why it is the case.

## Questions

- Do all models use gold mention spans?
