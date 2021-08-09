'''
Run all baselines against all versions of the corpus.

Usage:
  run_baselines.py [--n_jobs=<n>] --out_dir=<p> <inp_paths>...
'''

from docopt import docopt
from config import scorer
import os
from cort.core.corpora import Corpus
import codecs
import subprocess
from baselines import RandomAntecedent, RandomAgglomeration, OneClusterBaseline, HeadMatchBaseline
from joblib import Parallel, delayed


def main(inp_paths, out_dir, n_jobs):
    os.makedirs(out_dir, exist_ok=True)
    run_and_evaluate(RandomAntecedent(),inp_paths, out_dir, n_jobs)
    run_and_evaluate(RandomAgglomeration(),inp_paths, out_dir, n_jobs)
    run_and_evaluate(OneClusterBaseline(), inp_paths, out_dir, n_jobs)
    run_and_evaluate(HeadMatchBaseline(), inp_paths, out_dir, n_jobs)


def run_and_evaluate(system, inp_paths, out_dir, n_jobs):
    Parallel(n_jobs=n_jobs, verbose=1)(
        delayed(run_and_evaluate_file)(system, inp_path, out_dir)
        for inp_path in sorted(inp_paths)
    )


def run_and_evaluate_file(system, conll_path, out_dir):
    print('Running %s on %s ...' %(system.name, conll_path))
    out_basename = system.name + "__" + os.path.relpath(conll_path).replace('/', '__')

    with codecs.open(conll_path, 'r', 'utf-8') as f:
        corpus = Corpus.from_file(out_basename, f)
    new_docs = [system(doc) for doc in corpus]
    new_corpus = Corpus(out_basename, new_docs)

    conll_out_path = os.path.join(out_dir, out_basename)
    with codecs.open(conll_out_path, 'w', 'utf-8') as f:
        new_corpus.write_to_file(f)

    log_path = conll_out_path + '.log'
    with open(log_path, "w") as outfile:
        outfile.write('Evaluating system %s on %s\n' %(system.name, conll_path))
        outfile.flush()
        subprocess.check_call([scorer, 'all', conll_path, conll_out_path], stdout=outfile)


if __name__ == '__main__':
    args = docopt(__doc__)
    n_jobs = int(args.get('--n_jobs', '-1'))
    main(args['<inp_paths>'], args['--out_dir'], n_jobs)