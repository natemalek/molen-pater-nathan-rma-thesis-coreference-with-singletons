''' Extract results of from evaluation logs of e2e models

Usage:
    evaluate_all.py <log_dir> <out_path>
'''
import re
from glob import glob
import pandas as pd
from docopt import docopt
import os

def extract_results_from_log_file(path):
    recall_precision_regex = r'Recall:[\(\)\d/ ]+ ([\d\.]+)%\s+Precision:[\(\)\d/ ]+ ([\d\.]+)%'
    line_of_interest_regex = (r'Official result for (muc|bcub|ceafe)|' +
                                r'Identification of Mentions:\s+' + recall_precision_regex + '|' +
                                r'Coreference:(?:.+)\s+F1: ([\d\.]+)%|' +
                                r'Average F1 \(conll\): ([\d\.]+)%')
    with open(path) as f:
        s = f.read()
    matchers = list(re.finditer(line_of_interest_regex, s))
    print('\nFile: %s' %path)
    # print('\n'.join(m.group() for m in matchers))

    metric1_m, mention_identification_m, result1_m, metric2_m, _, result2_m, metric3_m, _, result3_m, f1_conll_m = matchers
    f1_conll = f1_conll_m.group(5)
    print('Average F1 (conll): %s' %f1_conll)

    return {
        'mention_r': mention_identification_m.group(2),
        'mention_p': mention_identification_m.group(3),
        'f1_' + metric1_m.group(1): result1_m.group(4),
        'f1_' + metric2_m.group(1): result2_m.group(4),
        'f1_' + metric3_m.group(1): result3_m.group(4),
        'f1_conll': f1_conll
    }


def main(log_dir, out_path):
    log_paths = os.path.join(log_dir, '*.log')
    results = []
    for log_path in glob(log_paths):
        try:
            (train_manipulation, sample_no, manipulation), = re.findall(
                r'eval-([\w_-]+)-on-.+__sample_(\d+)__([\w_-]+)__dev_test__m_gold_conll.log', log_path)
            try:
                results.append({
                    'system': 'e2e',
                    'sample': sample_no,
                    'train_manipulation': train_manipulation,
                    'manipulation': manipulation,
                    'dataset': 'dev_test',
                    'auto_or_gold': 'gold',
                    **extract_results_from_log_file(log_path)
                })
            except ValueError:
                print('Failed to parse file at %s. Ignored.' %log_path)
        except ValueError:
            print('Unexpected path: %s. Ignore.' %log_path)
        
    pd.DataFrame(results).to_csv(out_path, index=False)
    print('Results written to %s' %out_path)


if __name__ == '__main__':
    args = docopt(__doc__)
    main(args['<log_dir>'], args['<out_path>'])
    