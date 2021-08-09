'''
Annotation experiments with chunk-based and document-based design.

Usage:
  download.py <config> <out_path>
'''

import pandas as pd
from pyhocon import ConfigFactory
from docopt import docopt
from cort.core.corpora import Corpus
import shutil
from manipulations import token_mask
import os
from boto.mturk.question import HTMLQuestion
from boto.mturk.price import Price
import subprocess
import sys
import re
import random
from collections import defaultdict, Counter
import codecs
import csv
from config import scorer
import itertools
from glob import glob
from mturktools import open_mturk_connection, search_hits_by_title
from config import scorer
from tqdm import tqdm
import datetime

def download(conf, out_path):
    hit_title = conf.get_string('title')
    conn = open_mturk_connection(conf)
    hit_count, progress = 0, 0

    all_answers = []
    for h in tqdm(search_hits_by_title(conn, hit_title), desc="Downloading", unit="HIT"):
        assg = conn.get_assignments(h.HITId)
        progress += len(assg) / float(h.MaxAssignments)
        hit_count += 1
        for a in assg:
            (answers,) = a.answers # for some reason it's wrapped in a singleton list
            answers = dict((qfa.qid, qfa.fields[0]) for qfa in answers)
            all_answers.append(answers)
            
    pd.DataFrame(all_answers).to_csv(out_path, index=False)
    print("Completed %.1f of %d HITs" %(progress, hit_count))


if __name__ == '__main__':
    args = docopt(__doc__)
    conf = ConfigFactory.parse_file(args['<config>'])
    download(conf, args['<out_path>'])
