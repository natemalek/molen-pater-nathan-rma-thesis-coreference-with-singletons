''' Evaluate all cort models on the right corpus

Usage:
    eval_all.py [--n_jobs=<n>] --model_dir=<p> --out_dir=<p> <inp_paths>...
'''
from config import scorer
import os
from cort.core.corpora import Corpus
import codecs
import random
import subprocess
from cort_driver import predict, get_author_provided_model
from docopt import docopt
from joblib import Parallel, delayed
import itertools
from glob import glob
import re

dry_run = False

def main(model_dir, inp_paths, root_dir, n_jobs):
    os.makedirs(root_dir, exist_ok=True)
    jobs = itertools.chain(
        #run_and_evaluate_retrained_jobs('pair', model_dir, inp_paths, root_dir), # mention pair
        #run_and_evaluate_retrained_jobs('latent', model_dir, inp_paths, root_dir), # mention ranking
        run_and_evaluate_retrained_jobs('tree', model_dir, inp_paths, root_dir), # entity-mention
    )
    assert all(Parallel(n_jobs=n_jobs, verbose=1)(jobs))


# this is commented out because we only use gold mention
# def run_and_evaluate_jobs(system, model_path, inp_paths, root_dir):
#     out_dir = os.path.join(root_dir, system, 'auto')
#     os.makedirs(out_dir)
#     for inp_path in sorted(inp_paths):
#         yield delayed(run_and_evaluate_impl)(system, model_path, inp_path, out_dir)


def find_matching_model(system, retrained_models_dir, inp_path):
    model_paths = glob(os.path.join(retrained_models_dir, 'model-%s-*.obj' %system))
    corpus2model = {re.findall(r'model-\w+-(.+).obj$', p)[0]: p for p in model_paths}
    matching_models = [model_path for corpus, model_path in corpus2model.items() 
                       if corpus in inp_path.split('/')]
    assert len(matching_models) > 0, "Can't find the right model for input %s" %inp_path      
    assert len(matching_models) < 2, "Too many matching models for input %s" %inp_path
    return matching_models[0]


def run_and_evaluate_retrained_jobs(system, retrained_models_dir, inp_paths, root_dir):
    out_dir = os.path.join(root_dir, system, 'gold-retrained')
    os.makedirs(out_dir)
    for inp_path in sorted(inp_paths):
        model_path = find_matching_model(system, retrained_models_dir, inp_path)
        yield delayed(run_and_evaluate_impl)(system, model_path, inp_path, out_dir)


def run_and_evaluate_impl(system, model_path, inp_path, out_dir):
    out_basename = os.path.relpath(inp_path).replace('/', '__')
    out_path = os.path.abspath(os.path.join(out_dir, out_basename))
    log_path = out_path + '.log'
    cmd = [scorer, 'all', inp_path, out_path, 'none']
    print('Running %s on %s ...' %(system, inp_path))
    if not dry_run:
        predict(system, model_path, inp_path, out_path)

    with open(log_path, 'w') as f:
        f.write('Evaluating %s on %s\n' %(system, inp_path))
        f.flush()
        if not dry_run:
            subprocess.check_call(cmd, stdout=f)
    return out_path


if __name__ == '__main__':
    args = docopt(__doc__)
    main(args['--model_dir'], args['<inp_paths>'], 
         args['--out_dir'], int(args.get('--n_jobs') or -1))
