import os
import re
from cort.core.spans import Span
from cort.core.corpora import Corpus
from _collections import defaultdict
from nltk import cluster
import codecs
import subprocess
import shutil
import fileinput

# annotator = 'minh'
annotator = 'cltl'
metrics = 'ceafm'
scorer_path = 'reference-coreference-scorers/v8.01/scorer.pl'
dirs = [
        ('data/conll-2012-manipulated/mentions_instance_position-dev',
         'manual-annotation/%s/mentions_instance_position' %annotator),
        ('data/conll-2012-manipulated/position_events-dev',
         'manual-annotation/%s/position_events' %annotator),
        ]

def check_text_files(raw_dir, ann_dir):
    raw_fnames = set(p for p in os.listdir(raw_dir) if re.search(r'\.txt$', p))
    ann_fnames = set(p for p in os.listdir(ann_dir) if re.search(r'\.txt$', p))
    assert ann_fnames.issubset(raw_fnames)
    for fname in ann_fnames:
        with open(os.path.join(ann_dir, fname)) as f: ann_txt = f.read()
        with open(os.path.join(raw_dir, fname)) as f: raw_txt = f.read()
        assert ann_txt == raw_txt
        
def build_coref_set(path):
    clusters = defaultdict(set)
    with open(path) as f:
        for line in f:
            m = re.match('R\d+\tCoreference\s+\w+:(T\d+)\s+\w+:(T\d+)', line)
            if m:
                men1, men2 = m.group(1), m.group(2)
                c1, c2 = clusters[men1], clusters[men2] 
                c1.update(c2) # merge into one cluster
                for men in c2: # update mapping
                    clusters[men] = c1 
                c1.update({men1, men2})
    last_set_id = 0
    coref = {}
    for c in set(tuple(c) for c in clusters.values()):
        for men in c:
            coref[men] = last_set_id
        last_set_id += 1
    return coref

def read_mapping_file(path):
    mapping = {}
    with open(path) as f:
        for line in f:
            fields = line.strip().split('\t')
            mapping[fields[0]] = Span(int(fields[1]), int(fields[2]))
    return mapping

def cat(inp_paths, out_path):
    ''' Similar to Linux's cat command '''
    with open(out_path, 'w') as f_out,\
            fileinput.input(inp_paths) as f_inp:
        for line in f_inp: f_out.write(line)

def create_conll_files(raw_dir, ann_dir):
    ann_fnames = (p for p in os.listdir(ann_dir) if re.search(r'\.ann$', p))
    conll_files = []
    for fname in ann_fnames:
        coref = build_coref_set(os.path.join(ann_dir, fname))
        mapping_path = os.path.join(raw_dir, re.sub(r'\.ann$', '.mapping', fname))
        mapping = read_mapping_file(mapping_path)
        coref2 = dict((mapping[key], val) for key, val in coref.items() 
                      if key in mapping)
        inp_file = os.path.join(raw_dir, re.sub(r'\.ann$', '', fname))
        out_file = os.path.join(ann_dir, re.sub(r'\.ann$', '', fname))
        with codecs.open(inp_file, 'r', "utf-8") as f: corpus = Corpus.from_file('', f)
        assert len(corpus.documents) == 1
        doc = corpus.documents[0]
        doc.system_mentions = doc.annotated_mentions
        for m in doc.system_mentions:
            if m.span in coref2:
                m.attributes['set_id'] = str(coref2[m.span])
        with codecs.open(out_file, 'w', "utf-8") as f: corpus.write_to_file(f)
        conll_files.append((inp_file, out_file))
    return conll_files

if __name__ == '__main__':
    for raw_dir, ann_dir in dirs:
        check_text_files(raw_dir, ann_dir)
        paths = create_conll_files(raw_dir, ann_dir)
#         for gold, ann in paths:
#             cmd = '%s %s %s %s' %(scorer_path, metrics, gold, ann)
#             print('\n\n\n%s\n%s' %('='*80, cmd))
#             subprocess.run(cmd, shell=True)
        gold_paths, ann_paths = zip(*paths)
        gold_all_path = 'output/exp-manual-annotation-gold.conll'
        ann_all_path = 'output/exp-manual-annotation-ann.conll'
        cat(gold_paths, gold_all_path)
        cat(ann_paths, ann_all_path)        
        
        cmd = '%s %s %s %s' %(scorer_path, metrics, gold_all_path, ann_all_path)
        print('\n\n\n%s\n%s' %('='*80, cmd))
        subprocess.run(cmd, shell=True)
