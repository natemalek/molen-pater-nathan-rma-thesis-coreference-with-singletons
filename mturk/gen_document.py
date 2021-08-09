'''
Annotation experiments with chunk-based and document-based design.

Usage:
  gen_document.py <config>
'''

from pyhocon import ConfigFactory
from docopt import docopt
from cort.core.corpora import Corpus
import os
import sys
import random
import codecs
import csv
import itertools
from utils import glob_all
from glob import glob
from htmltools import Template, generate_html_for_sentences
from tqdm import tqdm

metrics = 'all'

def generate(conf):
    if conf.get_bool('is_local'):
        template = Template( # reuse chunk template because the only difference is in the data
            html_path='mturk/template/chunk-local.html',
            js_paths=['mturk/template/chunk.js', 'mturk/template/chunk-local.js'],
            css_path='mturk/template/chunk.css',
        )
    else:
        template = Template( # reuse chunk template because the only difference is in the data
            html_path='mturk/template/chunk.html',
            js_paths=['mturk/template/chunk.js'],
            css_path='mturk/template/chunk.css',
        )

    question_output_dir = conf.get_string('local_dir')
    input_paths = conf.get_list('input_paths')

    os.makedirs(question_output_dir, exist_ok=True)
    num_questions = 0
    for inp_path in glob_all(input_paths):
        sys.stdout.write('Processing %s...\n' %inp_path)
        with open(inp_path) as f:
            corpus = Corpus.from_file('', f)
        for doc in corpus.documents:
            out_fname = '%s-question-%03d.html' %(conf.get_string('experiment_name'), num_questions)
            out_path = os.path.join(question_output_dir, out_fname)
            generate_html_for_sentences(template, inp_path, out_path, conf, doc)
            sys.stdout.write('Written a question to %s\n' %out_path)
            num_questions += 1
    print('Written %d questions to %s' %(num_questions, question_output_dir))


if __name__ == '__main__':
    args = docopt(__doc__)
    conf = ConfigFactory.parse_file(args['<config>'])
    generate(conf)
