''' Create two kinds of variations of CoNLL-2012: one with mentions masked and 
the other with contexts masked.

Usage:
    mask_mentions_or_context.py <input_dir> <output_dir>
'''

import os
from data import DatasetPaths
from random import Random
from manipulations2 import ReplaceNames, MaskMentionK,\
    MaskContextK
from manipulations import Manipulation
from collections import OrderedDict, namedtuple
from joblib import Parallel, delayed
from docopt import docopt
import pandas as pd


ManipulationSpecs = namedtuple('ManipulationSpecs', ['paths', 'func'])


def main(inp_dir, out_dir):
    os.makedirs(out_dir, exist_ok=True)

    datasets = OrderedDict([
        ('orig', ManipulationSpecs(
            paths = DatasetPaths(os.path.join(out_dir, 'orig')),
            func = Manipulation()
        )),
    ])

    # load seeds from a file so that they, and hence the generated documents, won't change
    seeds = pd.read_csv('data/seeds.csv').set_index('transformation')
    for k in range(20, 101, 20):
        name = 'men_%d' %k
        datasets[name] = ManipulationSpecs(
            paths = DatasetPaths(os.path.join(out_dir, name)),
            func = MaskMentionK(k, seeds.seed[name])
        )
  
        name = 'nonmen_%d' %k
        datasets[name] = ManipulationSpecs(
            paths = DatasetPaths(os.path.join(out_dir, name)),
            func = MaskContextK(k, seeds.seed[name])
        )
    
    Parallel(n_jobs=-1, verbose=10)(
        call for name, specs in datasets.items()
        for call in manipulation_calls(inp_dir, name, specs)
    )


def manipulation_calls(inp_dir, name, specs):
    yield delayed(specs.func)(os.path.join(inp_dir, 'train'), specs.paths.train_path)
    yield delayed(specs.func)(os.path.join(inp_dir, 'dev'), specs.paths.dev_path)
    yield delayed(specs.func)(os.path.join(inp_dir, 'test-key'), specs.paths.test_path)


if __name__ == '__main__':
    args = docopt(__doc__)
    main(args['<input_dir>'], args['<output_dir>'])
    