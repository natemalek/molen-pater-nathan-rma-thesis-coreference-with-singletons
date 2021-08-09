''' Generate a script which when run will train all necessary deep-coref models

Usage:
    gencmd_train_all.py <conll_inp_dir> <bash_out_path>
'''

from docopt import docopt
import sys
import os
import re
from itertools import zip_longest


def main(conll_inp_dir, bash_out_path):
    subdirs = os.listdir(conll_inp_dir)
    with open(bash_out_path, 'wt') as f:
        f.write('BASH=${1-bash}\n')
        subdir_full_paths = [
            os.path.join(conll_inp_dir, subdir)
            for subdir in subdirs
            if re.match(r'[\w_\-]+$', subdir)
        ]
        it = iter(sorted(subdir_full_paths))
        for paths in zip_longest(it, it, fillvalue=''):
            paths = ' '.join(paths)
            f.write('$BASH scripts/deep-coref/train-multiple.job %s\n' %paths)
    print('Wrote %d commands to %s' %(len(subdirs), bash_out_path), file=sys.stderr)

if __name__ == '__main__':
    args = docopt(__doc__)
    main(args['<conll_inp_dir>'], args['<bash_out_path>'])