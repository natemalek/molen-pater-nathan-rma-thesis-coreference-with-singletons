'''
Unpack corpora stored in one *_conll file into a directory, one file for each document.
Automatically look recursively and mirror the directory structure found in input dir.

Usage:
  unpack_corpora.py <inp_dir> <out_dir>
'''
from docopt import docopt
from cort.core.corpora import Corpus
from baselines import copy_gold_annotations
import os
from joblib import delayed, Parallel

def main(inp_dir, out_dir):
    Parallel(n_jobs=16)(get_jobs(inp_dir, out_dir))

def get_jobs(inp_dir, out_dir):
    os.makedirs(out_dir)
    for fname in sorted(os.listdir(inp_dir)):
        inp_path = os.path.join(inp_dir, fname)
        base_name, ext = os.path.splitext(fname)
        out_path = os.path.join(out_dir, base_name)
        if os.path.isfile(inp_path) and inp_path.endswith('_conll'):
            yield delayed(extract_corpus)(inp_path, out_path, ext)
        elif os.path.isdir(inp_path):
            for j in get_jobs(inp_path, out_path):
                yield j

def simplify_name(s):
    return (s.replace('/', '_').replace(' ', '_')
             .replace('(', '').replace(')', '').replace(';', ''))

def extract_corpus(inp_path, out_dir, extension):
    print(inp_path, '->', out_dir)
    os.makedirs(out_dir)
    with open(inp_path) as f:
        corpus = Corpus.from_file("", f)
    for doc in corpus:
        copy_gold_annotations(doc)
        out_path = os.path.join(out_dir, simplify_name(doc.identifier) + extension)
        with open(out_path, 'wt') as f:
            f.write(doc.get_string_representation())

if __name__ == "__main__":
    args = docopt(__doc__)
    main(args['<inp_dir>'], args['<out_dir>'])