'''
Call CoreNLP's export tool to create files that deep-coref can digest.

Usage:
  export_datasets.py --command=<CMD> <inp_dir> <out_dir>
'''

from joblib import *
from docopt import docopt
import os, shutil, re, subprocess

def main(cmd, inp_dir, out_dir):
    shutil.rmtree(out_dir, ignore_errors=True)
    os.makedirs(out_dir)
    Parallel(n_jobs=-1)(
        delayed(subprocess.check_call)([
            cmd,
            os.path.join(inp_dir, transformation),
            os.path.join(out_dir, transformation)
        ])
        for transformation in os.listdir(inp_dir)
        if re.match(r'[\w_\-]+', transformation)
    )

if __name__ == '__main__':
    args = docopt(__doc__)
    main(args['--command'], args['<inp_dir>'], args['<out_dir>'])