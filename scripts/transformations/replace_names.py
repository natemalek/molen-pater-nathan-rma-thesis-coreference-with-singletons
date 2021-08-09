''' Replace names in CoNLL-2012.

Usage:
    replace_names.py [--types=<comma_sep_list>] <input_dir> <output_dir>
'''

import os
from data import DatasetPaths
from random import Random
from manipulations2 import ReplaceNames, RememberingStringMap, ReplaceByMaskedToken, RandomStringMap
from manipulations import Manipulation
from collections import OrderedDict, namedtuple
from joblib import Parallel, delayed
from docopt import docopt


ManipulationSpecs = namedtuple('ManipulationSpecs', ['func', 'name', 'paths'])


def main(types, inp_dir, out_dir):
    inp_paths = DatasetPaths(inp_dir, test_dir_name='test-key')
    name_and_path = lambda name: (name, DatasetPaths(os.path.join(out_dir, name)))
    transformations = [
        ManipulationSpecs(remove_external_knowledge, *name_and_path('no-external')),
        ManipulationSpecs(remove_internal_knowledge, *name_and_path('no-internal')),
        ManipulationSpecs(remove_string_matches, *name_and_path('no-match')),
        ManipulationSpecs(mask_names, *name_and_path('no-name')),
    ]
    if types:
        types = [t.strip() for t in types.split(',')]
        transformations = [tr for tr in transformations if tr.name in types]
    print('The following transformations will be executed: ' + str(transformations))
    for t in transformations:
        os.makedirs(t.paths.base_dir, exist_ok=True)
    Parallel(n_jobs=-1, verbose=10)(
        call for tr in transformations for call in tr.func(inp_paths, tr.paths)
    )


def remove_external_knowledge(inp_paths, out_paths):
    func = ReplaceNames(RememberingStringMap(52932))
    yield delayed(func)(inp_paths.train_path, out_paths.train_path)
    yield delayed(func)(inp_paths.dev_path, out_paths.dev_path)
    yield delayed(func)(inp_paths.test_path, out_paths.test_path)


def remove_internal_knowledge(inp_paths, out_paths):
    yield delayed(ReplaceNames(RememberingStringMap(32)))(inp_paths.train_path, out_paths.train_path)
    yield delayed(ReplaceNames(RememberingStringMap(3592)))(inp_paths.dev_path, out_paths.dev_path)
    yield delayed(ReplaceNames(RememberingStringMap(939)))(inp_paths.test_path, out_paths.test_path)

def remove_string_matches(inp_paths, out_paths):
    yield delayed(ReplaceNames(RandomStringMap(525729)))(inp_paths.train_path, out_paths.train_path)
    yield delayed(ReplaceNames(RandomStringMap(7723)))(inp_paths.dev_path, out_paths.dev_path)
    yield delayed(ReplaceNames(RandomStringMap(96235)))(inp_paths.test_path, out_paths.test_path)

def mask_names(inp_paths, out_paths):
    func = ReplaceNames(ReplaceByMaskedToken())
    yield delayed(func)(inp_paths.train_path, out_paths.train_path)
    yield delayed(func)(inp_paths.dev_path, out_paths.dev_path)
    yield delayed(func)(inp_paths.test_path, out_paths.test_path)


if __name__ == '__main__':
    args = docopt(__doc__)
    main(args['--types'], args['<input_dir>'], args['<output_dir>'])