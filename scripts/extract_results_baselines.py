'''
Extract results from the log files of baselines and put into a CSV file

Usage:
  extract_results_baselines.py --out=<fn> <log_paths>...
'''

import re
from utils import grouper
import pandas as pd
from utils import match_with_line_no
import os
from utils import extract_results_official_scorer_log_file
from docopt import docopt


def main(log_paths, out_path):
    data = [extract_data(log_path) for log_path in log_paths]
    pd.DataFrame(data).to_csv(out_path, index=False)
    print('Results written to %s' %out_path)


def extract_data(log_path):
    with open(log_path) as f:
        content = f.read()
    info_m = re.match(r'Evaluating system ([\w\-]+) on .+(sample_\d+)/((?:no-)?[\w\d_]+)/(dev_test)\.m_(auto|gold)_conll', content)
    print('File:', log_path)
    print('Extracted info:', info_m.groups())
    return {
        'system': info_m.group(1),
        'sample': info_m.group(2),
        'manipulation': info_m.group(3),
        'dataset': info_m.group(4),
        'auto_or_gold': info_m.group(5),
        **extract_results_official_scorer_log_file(log_path)
    }


if __name__ == '__main__':
    args = docopt(__doc__)
    main(args['<log_paths>'], args['--out'])