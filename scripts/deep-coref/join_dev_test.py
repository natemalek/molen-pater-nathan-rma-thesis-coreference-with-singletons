'''
Join dev and test sets into dev_test
Input: a folder with "train", "dev", "test" subfolders
Output: a new folder with the same structure but "dev" and "test" are merged into "test"
and a new development set is sampled from "train".

Usage:
  join_dev_test.py <inp_dir> <out_dir>
'''

import re
from docopt import docopt
import os
import shutil
import random


def divide_new_train_dev(old_train_dir):
    fnames = [fname for fname in os.listdir(old_train_dir) if fname.endswith('_conll')]
    rng = random.Random(23529)
    rng.shuffle(fnames)
    split_pos = int(len(fnames) * 0.9)
    new_train = set(fnames[:split_pos])
    new_dev = set(fnames[split_pos:])
    return new_train, new_dev


def main(inp_dir, out_dir):
    new_train, new_dev = divide_new_train_dev(os.path.join(inp_dir, 'men_100', 'train'))
    for transformation in os.listdir(inp_dir):
        if re.match(r'[\w\-_]+', transformation):
            child_inp_dir = os.path.join(inp_dir, transformation)
            child_out_dir = os.path.join(out_dir, transformation)
            print(child_inp_dir)

            train_inp = os.path.join(child_inp_dir, 'train')
            copy_dir(train_inp, os.path.join(child_out_dir, 'train'), subset=new_train)
            copy_dir(train_inp, os.path.join(child_out_dir, 'dev'), subset=new_dev)
            copy_dir(os.path.join(child_inp_dir, 'dev'),   os.path.join(child_out_dir, 'test'))
            copy_dir(os.path.join(child_inp_dir, 'test'),  os.path.join(child_out_dir, 'test'))


def copy_dir(inp_dir, out_dir, subset=None):
    os.makedirs(out_dir, exist_ok=True)
    for fname in os.listdir(inp_dir):
        if fname.endswith('_conll') and (subset is None or fname in subset):
            inp_path = os.path.join(inp_dir, fname)
            out_path = os.path.join(out_dir, fname)
            os.symlink(inp_path, out_path)


if __name__ == '__main__':
    args = docopt(__doc__)
    main(args['<inp_dir>'], args['<out_dir>'])