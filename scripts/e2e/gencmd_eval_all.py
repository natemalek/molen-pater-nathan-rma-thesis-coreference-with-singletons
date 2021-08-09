''' Generate e2e configurations and a script which will evaluate models on all CoNLL files
in the specified directory.

Usage:
    gencmd_eval_all.py --suffix=<suffix> <conll_inp_dir> <json_inp_dir> <bash_out_dir> <log_out_dir>
'''

import os
import stat
import subprocess
import shutil
import sys
from docopt import docopt
from e2e_utils import E2eConfig
from utils import grouper_variable_length
import re
from tqdm import tqdm

suffix = ''
ds_name = 'dev_test'
eval_src_default_conf = 'eval-gold-mention-spans'


def main(conll_inp_dir, json_inp_dir, eval_bash_dir, log_out_dir):
    conll_inp_dir = os.path.abspath(conll_inp_dir)
    json_inp_dir = os.path.abspath(json_inp_dir)

    eval_confs = append_experiment_configurations(conll_inp_dir, json_inp_dir)
    write_eval_bash_scripts(eval_bash_dir, eval_confs, log_out_dir)
    print('Evaluation script written to: %s' %eval_bash_dir)


def iterate_conll_and_json_files(conll_dir, json_dir):
    for fname in sorted(os.listdir(conll_dir)):
        conll_path = os.path.join(conll_dir, fname)
        if os.path.isfile(conll_path):
            if conll_path.endswith('conll'):
                json_path = os.path.join(json_dir, fname + '.jsonlines')
                yield conll_path, json_path
        else:
            json_path = os.path.join(json_dir, fname)
            assert os.path.isdir(json_path)
            for ret in iterate_conll_and_json_files(conll_path, json_path):
                yield ret


def find_train_conf(conf, transformation):
    matching_keys = [key for key in conf.keys()
        if key.startswith('train-') and ('gold-retrain' in key) and key.endswith(suffix)
            and ('-%s-' % transformation) in key]
    assert len(matching_keys) > 0, "Key not found for transformation %s" % transformation
    assert len(matching_keys) < 2, "More than one key found for transformation %s" % transformation
    return matching_keys[0]


def append_experiment_configurations(conll_dir, json_dir):
    '''
    Add evaluation settings to e2e's config file.
    '''
    eval_confs = []
    with E2eConfig() as conf:
        eval_paths = []
        for conll_path, json_path in tqdm(iterate_conll_and_json_files(conll_dir, json_dir)):
            out_basename = os.path.relpath(conll_path).replace('/', '__').replace('.', '__')
            transformation, = re.findall(r'/([\w\-]+)/\w+\.\w+_conll$', conll_path)
            train_gold_retrain_conf = find_train_conf(conf, transformation)
            eval_conf_name = 'eval-%s-on-%s' %(transformation, out_basename)
            conf.add_eval_conf(eval_conf_name, train_gold_retrain_conf, json_path, conll_path)
            eval_confs.append(eval_conf_name)
        num_configs = len(eval_confs)
        print('Wrote %d configurations to %s' %(num_configs, conf.path))
    return eval_confs


def write_eval_bash_scripts(eval_bash_dir, conf_names, log_out_dir):
    os.makedirs(eval_bash_dir)
    for group_no, conf_name_group in enumerate(grouper_variable_length(conf_names, 24)):
        cmd_path = os.path.join(eval_bash_dir, '%02d.job' % group_no)
        with open(cmd_path, 'wt') as f:
            f.write('''#!/bin/bash
#SBATCH -t 2-00:00:00

. scripts/setup-cartesius.sh
. output/e2e/venv/bin/activate

cd e2e-coref
''')
            for conf_name_subgroup in grouper_variable_length(conf_name_group, 4):
                for conf_name in conf_name_subgroup:
                    log_path = os.path.join(log_out_dir, conf_name + '.log')
                    f.write('python -u test_single.py %s | tee ../%s &\n' %(conf_name, log_path))
                f.write('wait\n')
            f.write('deactivate\n')


if __name__ == '__main__':
    args = docopt(__doc__)
    suffix = args['--suffix']
    main(args['<conll_inp_dir>'], args['<json_inp_dir>'], 
         args['<bash_out_dir>'], args['<log_out_dir>'])