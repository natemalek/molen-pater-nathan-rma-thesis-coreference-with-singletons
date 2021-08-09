''' Extract results of from evaluation logs of MTurk experiments

Usage:
    extract_results.py --out=<out_path> <log_file>...
'''
import re
from glob import glob
import pandas as pd
from docopt import docopt
import os
import numpy as np
from collections import OrderedDict


def extract_results_from_log_file(path_or_file, verbose=False):
    recall_precision_regex = r'Recall:[\(\)\d/ ]+ ([\d\.]+)%\s+Precision:[\(\)\d/ ]+ ([\d\.]+)%'
    line_of_interest_regex = '|'.join([r'METRIC (muc|bcub|ceafe):',
                                       r'Identification of Mentions:\s+' + recall_precision_regex,
                                       r'Coreference:(?:.+)\s+F1: ([\d\.]+)%'])
    if hasattr(path_or_file, 'read'):
        s = path_or_file.read()
    else: 
        if verbose:
            print('File: %s' %path_or_file)
        with open(path_or_file) as f:
            s = f.read()
    matchers = list(re.finditer(line_of_interest_regex, s))
    if verbose:
        print('\n'.join(m.group() for m in matchers))

    metric1_m, mention_identification_m, result1_m, metric2_m, _, result2_m, _, _, metric3_m, _, result3_m, _ = matchers
    f1_conll = (float(result1_m.group(4)) + float(result2_m.group(4)) + float(result3_m.group(4))) / 3
    return OrderedDict([
        ('mention_r', mention_identification_m.group(2)),
        ('mention_p', mention_identification_m.group(3)),
        ('f1_' + metric1_m.group(1), result1_m.group(4)),
        ('f1_' + metric2_m.group(1), result2_m.group(4)),
        ('f1_' + metric3_m.group(1), result3_m.group(4)),
        ('f1_conll', f1_conll),
    ])


def main(log_paths, out_path):
    results = []
    for log_path in log_paths:
        manipulation, = re.findall(r'/([-\w]+).log$', log_path)
        try:
            results.append({
                'system': 'human',
                'manipulation': manipulation,
                'dataset': 'dev',
                'auto_or_gold': 'NA',
                **extract_results_from_log_file(log_path)
            })
        except ValueError:
            print('Failed to parse %s. Ignored.' %log_path)
        
    pd.DataFrame(results).to_csv(out_path, index=False)
    print('Results written to %s' %out_path)


if __name__ == '__main__':
    args = docopt(__doc__)
    main(args['<log_file>'], args['--out'])
    