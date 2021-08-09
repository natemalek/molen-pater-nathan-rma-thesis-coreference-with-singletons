'''
Score individual submissions received from Google Form.

Usage:
  evaluate_full_annotation.py --out=<output_dir> <input>...
'''

import pandas as pd
from docopt import docopt
from config import scorer
import subprocess
from mturk.mturktools import *
import os
import tempfile
from mturk.gformtools import *
from mturk.extract_results import extract_results_from_log_file
import sys
from tempfile import mkstemp

def read_annotations(csv_paths):
    anns1 = pd.concat([pd.read_csv(adhoc_fix(p)) for p in csv_paths], sort=False)
    anns2 = anns1.Annotations.apply(unpack_json)
    anns = pd.concat([anns1, anns2], axis=1)
    # sometimes people submit the same answer twice, we'll keep only the last submission 
    anns = anns.drop_duplicates(['Document', 'Username'], keep='last')
    # fix error due to copying and annotation tool bug
    anns['Timestamp_dt'] = pd.to_datetime(anns.Timestamp)
    anns['events'] = anns['events'].apply(lambda s: s.replace(' ', '') if isinstance(s, str) else None)
    anns['chains'] = anns['chains'].apply(lambda s: s.replace(' ', '') if isinstance(s, str) else None)

    # These lines are from Minh's original code; it looks to me like they are there to fix an error
    # that was later corrected (after 2019-04-18). I comment these out because 
    # getting chains from events wasn't working with 'skip mention' event
    #anns['chains_from_events'] = anns.events.apply(chains_str_from_events)
    #anns['chains'] = anns.apply(lambda row: (row['chains_from_events'] 
    #                            if (str(row['Timestamp_dt']) < '2019-04-18') and row['events'] 
    #                            else row['chains']), axis=1)



    anns['transformation'] = anns.conll_file.str.extract(r'/([\w-]+)/\s*(?:dev|test)')
    # there's no difference between using auto or gold because humans don't see our syntactic and semantic annotations
    # some *.auto_conll files are missing so I replace them with the *.gold_conll equivalence
    anns['conll_file'] = anns.conll_file.str.replace('auto_conll', 'gold_conll')

    filtered_anns = anns[anns.chains.notna() & (anns.chains != '')]
    if len(filtered_anns) != len(anns):
        print('Ignoring %d rows because of missing chains' %(len(anns)-len(filtered_anns)), file=sys.stderr)
    return filtered_anns

def main(csv_paths, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    anns = read_annotations(csv_paths)
    results = pd.DataFrame([
        {
            'transformation': name,
            **evaluate_submissions(group, os.path.join(out_dir, name))
        }
        for name, group in anns.groupby('transformation')
    ])
    results.to_csv(os.path.join(out_dir, "results.csv"), index=False, header=True)


def evaluate_submissions(df, out_base_path=None, proj_dir='.', verbose=0):
    if out_base_path is None:
        _, out_base_path = mkstemp()
    path_gold = out_base_path + '.gold_conll'
    path_ann = out_base_path + ".ann_conll"
    out_path = out_base_path + '.log'
    generate_conll_files_for_dataframe(df, path_gold, path_ann, proj_dir, verbose)
    run_evaluation_script(path_gold, path_ann, out_path, proj_dir)

    return pd.Series(extract_results_from_log_file(out_path))


def run_evaluation_script(path_gold, path_ann, out_path, proj_dir):
    cmd = [os.path.join(proj_dir, scorer), 'all', path_gold, path_ann, 'none']
    with open(out_path, 'w') as f:
        subprocess.call(cmd, stdout=f)


if __name__ == "__main__":
    args = docopt(__doc__)
    main(args['<input>'], args['--out'])
