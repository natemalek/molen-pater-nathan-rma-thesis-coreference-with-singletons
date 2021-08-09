''' Extract the results of deep-coref from log files

Usage:
    extract_results.py --out=<p> <log_paths>...
'''
import os
import re
import pandas as pd
from docopt import docopt


def main(log_paths, out_path):
    results = []
    for log_path in log_paths:
        name_m = re.search(r"/(sample_\d+)/([\w\-]+).log$", log_path)
        if name_m:
            sample, manipulation = name_m.groups()
            with open(log_path) as f:
                lines = f.readlines()
            f1_line, = [line for line in lines if line.startswith('test - MUC')]
            matches = re.findall(r'(\w+):? ([\d\.]+)+', f1_line)
            f1_scores = {
                'f1_' + name.lower() : float(score)
                for name, score in matches
            }

            results.append({
                'system': 'deep-coref',
                'sample': sample,
                'manipulation': manipulation,
                'dataset': 'dev+test',
                'auto_or_gold': 'gold',
                **f1_scores
            })
        else:
            print("Unsupported name pattern, ignored one path: %s" %log_path)
    pd.DataFrame(results).to_csv(out_path, index=False)
    print('Results written to file %s' %out_path)


if __name__ == '__main__':
    args = docopt(__doc__)
    main(args['<log_paths>'], args['--out'])