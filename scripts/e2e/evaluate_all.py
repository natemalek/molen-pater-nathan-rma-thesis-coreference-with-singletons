''' Evaluate all trained e2e models

Usage:
    evaluate_all.py [--pattern=<p>] [--suffix=<s>] <out_dir>
'''
import re
import subprocess
from joblib import Parallel, delayed
import os
from docopt import docopt

model_dir = 'e2e-coref/logs'

def main(suffix, pattern, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    configs = extract_config_names(suffix, pattern)
    Parallel(n_jobs=4, verbose=1)(
        delayed(test_single)(config, out_dir) for config in configs
    )


def test_single(config, out_dir):
    log_path = os.path.join(out_dir, config + '.log')
    cmd = 'scripts/e2e/test-single.job %s &> %s' %(config, log_path)
    print(cmd)
    subprocess.call(cmd, shell=True)


def extract_config_names(suffix, pattern):
    configs = []
    for fname in os.listdir(model_dir):
        if ((not suffix or re.match(r'eval-\S+-%s-\w+' %re.escape(suffix), fname)) and
            (not pattern or re.search(pattern, fname))):
            configs.append(fname)
    return configs


if __name__ == '__main__':
    args = docopt(__doc__)
    main(args['--suffix'], args['--pattern'], args['<out_dir>'])