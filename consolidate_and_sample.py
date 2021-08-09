'''Sample (shrink training corpus) and consolidate CoNLL-2012.

Usage:
    consolidate_and_sample.py <input_dir> <output_dir> <sample_size>
'''

from collections import defaultdict
from consolidate_copora import copy_subfolder, copy_files
import random
import os
import shutil
from glob import glob
from docopt import docopt
import re


def count_genres(inp_dir):
    paths = glob(os.path.join(inp_dir, 'orig', 'train', '*m_gold_conll'))
    fnames = [os.path.basename(path) for path in paths]
    genre_counts = defaultdict(int)
    for fname in fnames:
        genre = fname.split("_")[0]
        source = fname.split("_")[1]
        genre_counts[(genre, source)]+=1
    return genre_counts

def sample_genres(inp_dir, k):
    '''
    Given an inp dir and a value of k, generates a list of filenames k/100 the size of the original
    file list, balanced for genre and sub-genre
    '''
    paths = glob(os.path.join(inp_dir, 'orig', 'train', '*m_gold_conll'))
    fnames = [os.path.basename(path) for path in paths]
    genre_file_lists = defaultdict(list)
    for fname in fnames:
        genre = fname.split("_")[0]
        source = fname.split("_")[1]
        genre_file_lists[(genre, source)].append(fname)
    genre_samples = defaultdict(list)
    
    for genre, l in genre_file_lists.items():
        count = len(l)
        sample_size = int(count * k/100)
        genre_samples[genre] = random.sample(l, sample_size)

    return genre_samples
    
def sample_by_genre(inp_dir, out_dir, k):
    '''
    Given a corpus and a percentage value k, creates a consolidated training corpus that is k/100
    the size of the original, balanced for genre and sub-genre/source.
    '''
    genre_samples = sample_genres(inp_dir, k)
    train_inp_paths = []
    for genre, fname_list in genre_samples.items():
        train_inp_paths += fname_list

    print(f"inp_dir: {inp_dir}, out_dir: {out_dir}")
    shutil.rmtree(out_dir, ignore_errors=True)
    
    for corpus_fname in os.listdir(inp_dir): # iterates through men_20, men_40, ...
        print(f"corpus_fname: {corpus_fname}")
        inp_corpus_path = os.path.join(inp_dir, corpus_fname)
        print(f"inp_corpus_path: {inp_corpus_path}")
        out_corpus_path = os.path.join(out_dir, corpus_fname)
        if os.path.isdir(inp_corpus_path):
            print(f"True: is_path {inp_corpus_path}")
            os.makedirs(out_corpus_path)
            
            copy_subfolder_sample(inp_corpus_path, out_corpus_path, 'train', 'gold', '', train_inp_paths)
            copy_subfolder(inp_corpus_path, out_corpus_path, 'dev', 'gold', '')
            copy_subfolder(inp_corpus_path, out_corpus_path, 'test', 'gold', '')
            copy_subfolder(inp_corpus_path, out_corpus_path, ['dev', 'test'], 'gold', '')
    
def copy_subfolder_sample(inp_corpus_path, out_corpus_path, ds_name, conll_type, fname_prefix, train_inp_paths):
    '''
    Adapted from copy_subfolder. Only intended for use on train corpus in generating a shrunk-version.
    train_inp_paths is a list of basename paths of files to be included.
    '''
    
    fname_pattern = '{fname_prefix}*.m_{conll_type}_conll'.format(**locals())
    inp_paths = []
    for path in train_inp_paths:
        full_path = os.path.join(inp_corpus_path, ds_name, path)
        if os.path.exists(full_path):
            inp_paths.append(full_path)
        else:
            print(f"No such file: {full_path}")
    inp_paths = sorted(inp_paths)
        
    out_path = '{out_corpus_path}/{ds_name}.m_{conll_type}_conll'.format(**locals())
    print('Copying %s (%s) -> %s' %(inp_corpus_path, ds_name, out_path))
    copy_files(inp_paths, out_path)

def main(inp_dir, out_dir, k):
    sample_by_genre(inp_dir, out_dir, k)
    
if __name__ == '__main__':
    args = docopt(__doc__)
    main(args['<input_dir>'], args['<output_dir>'], int(args['<sample_size>']))