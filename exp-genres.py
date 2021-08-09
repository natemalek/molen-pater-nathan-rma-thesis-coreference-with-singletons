import subprocess
import sys
import os
from config import datasets, algorithms, genres, score_pattern, OriginalDataset,\
    MentionInstancePositionSyntaxDataset
import re
import itertools
import shutil
from collections import defaultdict
from cort.core.corpora import Corpus
import numpy as np
import codecs
from utils import print_csv2, print_csv, get_chains, find_sentence
from collections import Counter

my_datasets = datasets
dry_run = False # turn on for debugging

def prepare_datasets():
    paths = defaultdict(dict)
    for ds in my_datasets:
        for genre in genres:
            path = os.path.join('output', 'exp-genre', genre, ds.name + '-dev')
            os.makedirs(path, exist_ok=True)
            paths[genre][ds] = path
    for ds in my_datasets:
        for fname in os.listdir(ds.dev_path):
            if re.search(r'\_conll$', fname):
                genre = re.search(r'^(\w\w)_', fname).group(1)
                shutil.copy(os.path.join(ds.dev_path, fname), paths[genre][ds])
    return paths

def run_algorithms(paths):
    row_names = genres
    col_level1_names = [algo[0] for algo in algorithms]
    col_level2_names = [ds.name for ds in my_datasets]
    scores = []
    for genre in genres:
        row_level1 = []
        for algo_name, algo_script in algorithms:
            row_level2 = []
            for ds in my_datasets:
                log_path = 'output/exp-genre-%s-%s-%s.log' %(genre, ds.name, algo_name)
                cmd = ('scripts/%s %s > %s 2>&1' %(algo_script, 
                                                   os.path.abspath(paths[genre][ds]),
                                                   os.path.abspath(log_path)))
                sys.stderr.write('%s\n' %cmd)
                retcode = subprocess.call(cmd, shell=True)
                if retcode == 0:
                    with open(log_path) as f: log = f.read()
                    m = re.search(score_pattern, log)
                    score = float(m.group(1))
                    row_level2.append(score)
                else:
                    row_level2.append('err')
            row_level1.append(row_level2)
        scores.append(row_level1)
    print_csv2(row_names, col_level1_names, col_level2_names, scores)
    
def sublist_ignore_case(needle, haystack):
    needle_lower = [item.lower() for item in needle]
    haystack_lower = [item.lower() for item in haystack]
    for i in range(len(haystack)-len(needle)+1):
        if haystack_lower[i] == needle_lower[0]:
            # don't iterate from 1 because an empty list will be judged as False
            match = all(haystack_lower[i+j] == needle_lower[j]
                        for j in range(len(needle_lower)))
            if match: 
                return True
    return False
    
def matches_previous_mention(idx, chain):
    mention_tokens = chain[idx].attributes['tokens']
    for i in range(idx):
        prev_mention_tokens = chain[i].attributes['tokens']
        if (sublist_ignore_case(mention_tokens, prev_mention_tokens) or 
            sublist_ignore_case(prev_mention_tokens, mention_tokens)):
            return True
    return False
    
def classify_pronouns(pronoun_counter, num_mentions):
    type2pronoun = {
        '1st': {'i', 'we', 'me', 'us', 'my', 'our', 'mine', 'ours', 'myself',
                'we all', 'ourselves'},
        '2nd': {'you', 'your', 'yours', 'you all', 'you both', 'yourselves'},
        '3rd': {'he', 'she', 'it', 'they', 'his', 'her', 'hers', 'their', 
                'theirs', 'its', 'them', 'him', 'itself', 'herself', 
                'himself', 'themselves', 'they all', 'them all', 'they both', 
                'they themselves'},
    }
    type_counter = Counter()
    others = set()
    for s in pronoun_counter:
        if s in type2pronoun['1st']:
            type_counter['1st'] += pronoun_counter[s]
        elif s in type2pronoun['2nd']:
            type_counter['2nd'] += pronoun_counter[s]
        elif s in type2pronoun['3rd']:
            type_counter['3rd'] += pronoun_counter[s]
        else:
            type_counter['other'] += pronoun_counter[s]
            others.add(s)
    print('Ignored %d spurious "pronouns", %d occurrences in total (%.1f%% of all mentions): %s' 
          %(len(others), type_counter['other'], 
            100.0*type_counter['other']/num_mentions, str(others)))
    return type_counter
    
def measure_genres(paths):
    rows = genres
    cols = ['#mentions', '#chains', '#chains_per_doc', 
            'avg(#mentions_in_chain)', 'std(#mentions_in_chain)', 
            '#non_matching_mentions', 'non_matching_mentions(%)',
            'proper_name(%)', 'common_noun(%)', 'pronoun(%)', 
            'demonstrative_pronoun(%)', 'verb(%)', 
            '1st_person', '2nd_person', '3rd_person',
            'person(%)', 'object(%)', 'unknown_semantic_class(%)',
            'within_5_sents(%)', 'within_6_sents(%)', 'within_7_sents(%)', 
            'within_8_sents(%)', 'within_9_sents(%)', 'within_10_sents(%)', 
            '#sentences_per_doc']
    vals = []
    for genre in paths:
        distances = []
        num_sentences_in_doc = [] 
        num_chains_in_doc = []
        num_docs = 0
        num_mentions_in_chain = []
        num_non_matching_mentions = 0
        type_counter = Counter()
        semantic_class_counter = Counter()
        pronoun_counter = Counter() 
        dir_ = paths[genre][OriginalDataset]
        for fname in os.listdir(dir_):
            path = os.path.join(dir_, fname)
            with codecs.open(path, 'r', 'utf-8') as f: 
                corpus = Corpus.from_file(fname, f)
            for doc in corpus.documents:
                num_docs += 1
                chains = get_chains(doc)
                num_sentences_in_doc.append(len(doc.sentence_spans))
                num_chains_in_doc.append(len(chains))
                for chain in chains:
                    num_mentions_in_chain.append(len(chain))
                    for idx in range(1, len(chain)):
                        if not matches_previous_mention(idx, chain):
                            num_non_matching_mentions += 1
                    for mention in chain: 
                        type_counter[mention.attributes['type']] += 1
                        if mention.attributes['type'] == 'PRO':
                            pronoun_counter[mention.attributes['tokens_as_lowercase_string']] += 1
                        semantic_class_counter[mention.attributes['semantic_class']] += 1
                    sent_ids = [find_sentence(m.span, doc) for m in chain]
                    distances.extend(sent_ids[i]-sent_ids[i-1] 
                                     for i in range(1, len(sent_ids)))

        distances = np.array(distances)
        num_chains_in_doc = np.array(num_chains_in_doc)
        num_mentions_in_chain = np.array(num_mentions_in_chain)
        num_mentions = num_mentions_in_chain.sum()
        pronoun_type_counter = classify_pronouns(pronoun_counter, num_mentions)
        vals.append([num_mentions, num_chains_in_doc.sum(), num_chains_in_doc.mean(),
                     num_mentions_in_chain.mean(), num_mentions_in_chain.std(),
                     num_non_matching_mentions,
                     100.0*num_non_matching_mentions/num_mentions,
                     100.0*type_counter['NAM']/num_mentions,
                     100.0*type_counter['NOM']/num_mentions,
                     100.0*type_counter['PRO']/num_mentions,
                     100.0*type_counter['DEM']/num_mentions,
                     100.0*type_counter['VRB']/num_mentions,
                     100.0*pronoun_type_counter['1st']/num_mentions,
                     100.0*pronoun_type_counter['2nd']/num_mentions,
                     100.0*pronoun_type_counter['3rd']/num_mentions,
                     100.0*semantic_class_counter['PERSON']/num_mentions,
                     100.0*semantic_class_counter['OBJECT']/num_mentions,
                     100.0*semantic_class_counter['UNKNOWN']/num_mentions,
                     100.0*(distances < 5).sum()/len(distances),
                     100.0*(distances < 6).sum()/len(distances),
                     100.0*(distances < 7).sum()/len(distances),
                     100.0*(distances < 8).sum()/len(distances),
                     100.0*(distances < 9).sum()/len(distances),
                     100.0*(distances < 10).sum()/len(distances),
                     np.mean(num_sentences_in_doc),])
    print_csv(rows, cols, vals, decimal_places=1)

if __name__ == '__main__':
    paths = prepare_datasets()
    run_algorithms(paths)
#     measure_genres(paths)
    