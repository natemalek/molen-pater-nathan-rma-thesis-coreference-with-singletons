'''
Extract results from the log files of Stanford sieve and put into a CSV file

Usage:
  extract_results_stanford_sieve.py --out=<fn> <log_paths>...
'''

from utils import match_with_line_no, grouper
import re
from docopt import docopt
import pandas as pd
import os


def main(log_paths, out_path):
    results = [extract_data(log_path) for log_path in log_paths]
    pd.DataFrame(results).to_csv(out_path, index=False)
    print('Results written to %s' %out_path)


def extract_data(log_path):
    with open(log_path) as f:
        content = f.read()
    info_m = re.match(r'Evaluating on .+(sample_\d+)/((?:no-)?[\w\d_]+)/(dev_test)\.m_(auto|gold)_conll', content)
    line_regex = (r'Identification of Mentions:\s+Recall:[\(\)\d/ ]+ ([\d\.]+)%\s+Precision:[\(\)\d/ ]+ ([\d\.]+)%|' +
                    re.escape('Final conll score ((muc+bcub+ceafe)/3) = ') + r'([\d\.]+)')
    with open(log_path) as f:
        matchers = list(re.finditer(line_regex, f.read()))
    print('File:', log_path)
    print('Extracted info:', info_m.groups(), list(m.group() for m in matchers))
    mention_identification_m, f1_conll_m = matchers
    return {
        'system': 'sieve',
        'sample': info_m.group(1),
        'manipulation': info_m.group(2),
        'dataset': info_m.group(3),
        'auto_or_gold': info_m.group(4),
        'mention_r': mention_identification_m.group(1),
        'mention_p': mention_identification_m.group(2),
        'f1_conll': float(f1_conll_m.group(3))
    }
    

if __name__ == '__main__':
    args = docopt(__doc__)
    main(args['<log_paths>'], args['--out'])
