'''
Run Stanford Sieve algorithm (Lee et al. 2013) on a set of documents,
produce the output and evaluation results.

Usage:
  run_stanford_sieve.py [--n_jobs=<n>] --out_dir=<p> <inp_paths>...
'''

import subprocess
import os
import re
from data import DatasetPaths
import pandas as pd
from collections import OrderedDict, defaultdict
from joblib import Parallel, delayed
from docopt import docopt


script_path = os.path.abspath('scripts/run_stanford_sieve_single.sh')


def main(inp_paths, out_dir, n_jobs):
    os.makedirs(out_dir, exist_ok=True)
    Parallel(n_jobs=n_jobs, verbose=1)(
        delayed(evaluate_single_corpus)(inp_path, out_dir)
        for inp_path in sorted(inp_paths)
    )


def evaluate_single_corpus(inp_path, out_dir):
    print('Running on %s ...' %inp_path)
    out_basename = os.path.relpath(inp_path).replace('/', '__')
    out_path = os.path.abspath(os.path.join(out_dir, out_basename))
    log_path = out_path + '.log'
    is_auto = str(inp_path.endswith('auto_conll'))
    cmd = [script_path, inp_path, is_auto, out_path]
    
    with open(log_path, "w") as outfile:
        outfile.write('Evaluating on %s\n' %inp_path)
        outfile.flush()
        subprocess.check_call(cmd, stdout=outfile, stderr=outfile)


if __name__ == '__main__':
    args = docopt(__doc__)
    n_jobs = int(args.get('--n_jobs', '-1'))
    main(args['<inp_paths>'], args['--out_dir'], n_jobs)
