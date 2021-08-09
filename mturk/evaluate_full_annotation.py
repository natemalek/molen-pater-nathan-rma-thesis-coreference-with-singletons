'''
Evaluate a set of annotations downloaded from Mechanical Turk or Google Form.
All mentions in a documention are expected to be annotated by a human 
(skipped mentions are considered singletons).
Print out metrics to CSV files in a directory.

Usage:
  evaluate_full_annotation.py [--gform] --out=<output_dir> <input>...
'''

import pandas as pd
from docopt import docopt
from config import scorer
import subprocess
from mturk.mturktools import *
import os
import tempfile
from mturk.gformtools import unpack_json


def main(csv_paths, out_dir, is_gform):
    anns = pd.concat([pd.read_csv(adhoc_fix(p)) for p in csv_paths])
    if is_gform:
        anns2 = anns.Annotations.apply(unpack_json)
        anns = pd.concat([anns, anns2], axis=1)
    print(anns[['chains', 'conll_file']].head())

    trans_dir = os.path.join(out_dir, 'transformations')
    os.makedirs(trans_dir, exist_ok=False)
    workers_dir = os.path.join(out_dir, 'workers')
    os.makedirs(workers_dir, exist_ok=False)

    anns['transformation'] = anns.conll_file.apply(extract_transformation)
    anns.groupby('transformation').apply(evaluate_transformation, trans_dir)
    anns.groupby('workerId').apply(evaluate_worker, workers_dir)


def evaluate_transformation(anns, out_dir):
    transformation, = anns.transformation.unique()
    path_gold = os.path.join(out_dir, transformation + '.gold_conll')
    path_ann = os.path.join(out_dir, transformation + ".ann_conll")
    out_path = os.path.join(out_dir, transformation + '.log')

    generate_conll_files_for_dataframe(anns, path_gold, path_ann)
    run_evaluation_script(path_gold, path_ann, out_path)


def evaluate_worker(anns, out_dir):
    workerId, = anns.workerId.unique()
    path_gold = os.path.join(out_dir, '%s.gold_conll' % workerId)
    path_ann = os.path.join(out_dir, '%s.ann_conll' % workerId)
    out_path = os.path.join(out_dir, '%s.log' % workerId)

    generate_conll_files_for_dataframe(anns, path_gold, path_ann)
    run_evaluation_script(path_gold, path_ann, out_path)


def run_evaluation_script(path_gold, path_ann, out_path):
    cmd = ' '.join([scorer, 'all', path_gold, path_ann, '>', out_path])
    subprocess.run(cmd, shell=True)


if __name__ == "__main__":
    args = docopt(__doc__)
    main(args['<input>'], args['--out'], args['--gform'])
