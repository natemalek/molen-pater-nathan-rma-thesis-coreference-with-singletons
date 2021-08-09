'''Submit HTML questions to Mechanical Turk

Usage:
  submit.py <config>
'''

import pandas as pd
from pyhocon import ConfigFactory
from docopt import docopt
from mturktools import open_mturk_connection
import os
from glob import glob
from tqdm import tqdm
from boto.mturk.question import HTMLQuestion
from boto.mturk.price import Price
import datetime
import traceback

def submit(conf):
    conn = open_mturk_connection(conf)
    html_paths = glob(os.path.join(conf.get_string('local_dir'), '*.html'))
    for path in tqdm(html_paths, desc="Submitting", unit="question"):
        with open(path) as f:
            html_content = f.read()
        try:
            conn.create_hit(
                    title=conf.get_string('title'),
                    description=conf.get_string('description'),
                    keywords=conf.get_string('keywords'),
                    duration=datetime.timedelta(days=conf.get_int('duration_days')),
                    max_assignments=conf.get_int('num_annotators_per_hit'),
                    question=HTMLQuestion(html_content, conf.get_int('frame_height')),
                    reward=Price(amount=conf.get_float('price_eur_per_hit')),
                    response_groups=('Minimal', 'HITDetail'),  # I don't know what response groups are
            )
        except:
            print('Submission of question "%s" failed' %path)
            traceback.print_stack()

    conn.close()

if __name__ == '__main__':
    args = docopt(__doc__)
    conf = ConfigFactory.parse_file(args['<config>'])
    submit(conf)