''' Generate a script which when run will train all necessary e2e models

Usage:
    gencmd_train_all.py <conll_inp_dir> <json_inp_dir> <suffix> <bash_out_path>
'''

import os
import stat
import subprocess
import shutil
import sys
from docopt import docopt
from utils import symlink_safe
from e2e_utils import E2eConfig


train_src_conf = 'train-gold-mention-spans'


def main(conll_inp_dir, json_inp_dir, suffix, train_bash_path):
    conll_inp_dir = os.path.abspath(conll_inp_dir)
    json_inp_dir = os.path.abspath(json_inp_dir)

    train_confs, _ = append_experiment_configurations(
        experiments_conf_path, conll_inp_dir, json_inp_dir, suffix)
    write_train_bash_script(train_bash_path, train_confs)
    print(train_bash_path)


def append_experiment_configurations(experiments_conf_path, conll_dir, json_dir, suffix):
    train_confs = []

    with E2eConfig() as conf:
        # this has the same content as train-gold-mention-spans but we give it 
        # an unique name so that it isn't trained multiple times
        auto_no_retrain_conf = 'train-orig-auto-%s' %suffix 
        conf.add_train_conf(auto_no_retrain_conf, train_src_conf, 
                json_dir + '/orig/train_auto.jsonlines',
                json_dir + '/orig/dev_test_auto.jsonlines',
                conll_dir + '/orig/dev_test.m_auto_conll')
        train_confs.append(auto_no_retrain_conf)

        for corpus_name in sorted(os.listdir(conll_dir)):
            conll_path = os.path.join(conll_dir, corpus_name)
            json_path = os.path.join(json_dir, corpus_name)
            if os.path.isdir(conll_path):
                assert os.path.isdir(json_path) 
                train_gold_retrain_conf = 'train-%s-gold-retrain-%s' %(corpus_name, suffix) 
                conf.add_train_conf(train_gold_retrain_conf, train_src_conf, 
                        json_dir + '/orig/train_gold.jsonlines',
                        json_dir + '/orig/dev_test_gold.jsonlines',
                        conll_dir + '/orig/dev_test.m_gold_conll')
                train_confs.append(train_gold_retrain_conf)

    print('Wrote %d configurations to %s' %(len(train_confs), experiments_conf_path), file=sys.stderr)
    return train_confs


def write_train_bash_script(cmd_path, conf_names):
    with open(cmd_path, 'wt') as f:
        f.write('BASH=${1-bash}\n')
        for conf_name in conf_names:
            f.write('$BASH scripts/e2e/train-single.job %s $2\n' %conf_name)
    print('Wrote %d commands to %s' %(len(conf_names), cmd_path), file=sys.stderr)


if __name__ == '__main__':
    args = docopt(__doc__)
    main(args['<conll_inp_dir>'], args['<json_inp_dir>'], args['<suffix>'], args['<bash_out_path>'])