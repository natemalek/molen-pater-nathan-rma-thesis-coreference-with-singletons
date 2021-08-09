import subprocess
import shutil
import os
import re
from collections import defaultdict
import codecs

def flatten(root_dir, flat_dir):
    assert os.path.exists(root_dir), 'Data dir not found: %s' %root_dir
    os.makedirs(flat_dir, exist_ok=True)
    for file_suf in ("auto_conll", "gold_conll"):
        matches = subprocess.check_output("find %s -name *%s" % (root_dir, file_suf), shell=True)
        matches = matches.decode().split('\n')[:-1]
        for match in matches:
            match_fields = match.split('/')
            new_path = os.path.join(flat_dir,match_fields[-4]+"_"+match_fields[-1])
            shutil.copyfile(match, new_path)
        os.makedirs(flat_dir + '-all', exist_ok=True)

def merge_key_to_auto_conll(gold_dir, auto_dir):
    mapping = defaultdict(list)
    for fname_auto in os.listdir(auto_dir):
        m = re.match(r'^(.+)\.\w+_auto_conll$', fname_auto)
        if m: mapping[m.group(1)].append(fname_auto)
    for fname_gold in os.listdir(gold_dir):
        m = re.match(r'^(.+)\.\w+_gold_conll$', fname_gold)
        if m: mapping[m.group(1)].append(fname_gold)
    for fname_auto, fname_gold in mapping.values():
        with codecs.open(os.path.join(auto_dir, fname_auto), encoding='utf-8') as f_auto, \
                codecs.open(os.path.join(gold_dir, fname_gold), encoding='utf-8') as f_gold, \
                codecs.open(os.path.join(gold_dir, fname_auto), 'w', encoding='utf-8') as f_auto_new:
            for line_auto, line_gold in zip(f_auto, f_gold):
                fields_auto = re.split('[ \t]+', line_auto)
                fields_gold = re.split('[ \t]+', line_gold)
                assert fields_auto[:4] == fields_gold[:4]
                if len(fields_auto) >= 6:
                    fields_auto[-1] = fields_gold[-1] 
                    line_auto = '\t'.join(fields_auto)
                f_auto_new.write(line_auto)

flatten("data/conll-2012/v4/data/train/data/english", "data/conll-2012-flat/train")
flatten("data/conll-2012/v4/data/development/data/english", "data/conll-2012-flat/dev")
flatten("data/conll-2012/v9/data/test/data/english", "data/conll-2012-flat/test")
flatten("data/conll-2012/v4/data/test/data/english", "data/conll-2012-flat/test-key")
merge_key_to_auto_conll("data/conll-2012-flat/test-key", "data/conll-2012-flat/test")