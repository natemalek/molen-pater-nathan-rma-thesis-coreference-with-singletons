''' Train all cort models

Usage:
    train_all.py [--num_processes=<n>] --type=<t> <consolidated_conll_dir> <out_dir>
'''
import os
from cort.core.corpora import Corpus
import codecs
import random
import subprocess
from cort_driver import train
from joblib import Parallel, delayed
import sys
import itertools
from docopt import docopt


def main(type_, inp_dir, out_dir, num_processes):
    assert type_ in ('pair', 'latent', 'tree'), "Invalid type: %s" %type_
    os.makedirs(out_dir, exist_ok=True)
    results = Parallel(n_jobs=num_processes, verbose=1)(train_jobs(type_, inp_dir, out_dir))
    assert all(results)


def train_jobs(system, inp_dir, out_dir):
    manipulations = sorted(os.listdir(inp_dir))
    for manipulation in manipulations:
        yield delayed(train_single_system)(system, inp_dir, out_dir, manipulation)


def train_single_system(system, inp_dir, out_dir, manipulation):
    conll_path = os.path.join(inp_dir, manipulation, 'train.m_gold_conll')
    out_model_path = os.path.join(out_dir, 'model-%s-%s.obj' %(system, manipulation))
    print('Training %s on %s ...' %(system, conll_path), file=sys.stderr)
    if train(system, os.path.abspath(conll_path), os.path.abspath(out_model_path)) == 0:
        print('Model written to %s' %out_model_path, file=sys.stderr)
    return out_model_path


if __name__ == '__main__':
    args = docopt(__doc__)
    main(args['--type'], args['<consolidated_conll_dir>'], args['<out_dir>'], 
         int(args.get('--num_processes') or 1))
