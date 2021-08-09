'''
Annotation experiments with chunk-based and document-based design.

Usage:
  gen_chunk.py <config>
'''

from pyhocon import ConfigFactory
from docopt import docopt
from cort.core.corpora import Corpus
import shutil
import os
import sys
import random
from collections import defaultdict
import codecs
import csv
import itertools
from glob import glob
from htmltools import Template, generate_html_for_sentences
from tqdm import tqdm
from utils import glob_all

metrics = 'all'

template = Template(
    html_path='mturk/template/chunk.html',
    js_path='mturk/template/chunk.js',
    css_path='mturk/template/chunk.css',
)


def _calculate_num_mentions(doc, sent_begin, sent_end):
    first_token_of_chunk = doc.sentence_spans[sent_begin].begin
    last_token_of_chunk = doc.sentence_spans[sent_end].end
    return sum(1 for m in doc.annotated_mentions
               if m.span.begin >= first_token_of_chunk and
               m.span.end <= last_token_of_chunk)


def generate(conf):
    question_output_dir = conf.get_string('local_dir')
    input_paths = conf.get_list('input_paths')
    max_sents = conf.get_int('max_num_sentences_in_chunk')
    max_mentions = conf.get_int('max_num_mentions_in_chunk')

    os.makedirs(question_output_dir, exist_ok=True)
    num_questions = 0
    for inp_path in glob_all(input_paths):
        sys.stdout.write('Processing %s...\n' % inp_path)
        with open(inp_path) as f:
            corpus = Corpus.from_file('', f)
        for doc in corpus.documents:
            sent_begin, sent_end = 0, -1
            while sent_end < len(doc.sentence_spans)-1:
                sent_end = sent_begin
                num_mentions = _calculate_num_mentions(doc, sent_begin, sent_end)
                while (sent_end < len(doc.sentence_spans) - 1 and
                        (max_sents <= 0 or sent_end-sent_begin+1 < max_sents) and
                        (max_mentions <= 0 or num_mentions < max_mentions)):
                    sent_end += 1  # add one sentence to the chunk
                    num_mentions = _calculate_num_mentions(doc, sent_begin, sent_end)

                if num_mentions >= 2:
                    out_path = os.path.join(question_output_dir, 'question-%03d.html' % num_questions)
                    generate_html_for_sentences(template, inp_path, out_path, conf, doc, sent_begin, sent_end)
                    sys.stdout.write('Written a question to %s\n' % out_path)
                    num_questions += 1

                # move half of the chunk forward
                sent_begin += max((sent_end - sent_begin + 1) // 2, 1)
    print('Written %d questions to %s' %(num_questions, question_output_dir))

if __name__ == '__main__':
    args = docopt(__doc__)
    conf = ConfigFactory.parse_file(args['<config>'])
    generate(conf)
