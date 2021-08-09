''' Replace names in CoNLL-2012.

Usage:
    replace_names.py <input_dir> <output_dir> [--genre]
'''
import os
import shutil
from glob import glob
from docopt import docopt
import re


def copy_folder(inp_dir, out_dir, fname_prefix):
    print(f"inp_dir: {inp_dir}, out_dir: {out_dir}")
    shutil.rmtree(out_dir, ignore_errors=True)
    for corpus_fname in os.listdir(inp_dir):
        print(f"corpus_fname: {corpus_fname}")
        inp_corpus_path = os.path.join(inp_dir, corpus_fname)
        print(f"inp_corpus_path: {inp_corpus_path}")
        out_corpus_path = os.path.join(out_dir, corpus_fname)
        if os.path.isdir(inp_corpus_path):
            print(f"True: is_path {inp_corpus_path}")
            os.makedirs(out_corpus_path)

            copy_subfolder(inp_corpus_path, out_corpus_path, 'train', 'auto', fname_prefix)
            copy_subfolder(inp_corpus_path, out_corpus_path, 'dev', 'auto', fname_prefix)
            copy_subfolder(inp_corpus_path, out_corpus_path, 'test', 'auto', fname_prefix)
            copy_subfolder(inp_corpus_path, out_corpus_path, ['dev', 'test'], 'auto', fname_prefix)

            copy_subfolder(inp_corpus_path, out_corpus_path, 'train', 'gold', fname_prefix)
            copy_subfolder(inp_corpus_path, out_corpus_path, 'dev', 'gold', fname_prefix)
            copy_subfolder(inp_corpus_path, out_corpus_path, 'test', 'gold', fname_prefix)
            copy_subfolder(inp_corpus_path, out_corpus_path, ['dev', 'test'], 'gold', fname_prefix)


def copy_subfolder(inp_corpus_path, out_corpus_path, ds_names, conll_type, fname_prefix):
    fname_pattern = '{fname_prefix}*.m_{conll_type}_conll'.format(**locals())
    inp_ds_names = ds_names if isinstance(ds_names, (list, tuple)) else [ds_names]
    out_ds_name = '_'.join(inp_ds_names)
    inp_paths = sorted([
        path
        for ds_name in inp_ds_names
        for path in glob(os.path.join(inp_corpus_path, ds_name, fname_pattern))
    ]) # sort to increase reproducibility
    out_path = '{out_corpus_path}/{out_ds_name}.m_{conll_type}_conll'.format(**locals())
    print('Copying %s (%s) -> %s' %(inp_corpus_path, ds_names, out_path))
    copy_files(inp_paths, out_path)


def copy_files(inp_paths, out_path):
    ''' Because Linux's cat command give "Argument list too long" error, 
    we use this method to copy file content '''
    with open(out_path, 'wb') as out_file:
        for inp_path in inp_paths:
            with open(inp_path, 'rb') as inp_file:
                shutil.copyfileobj(inp_file, out_file)


def main(inp_dir, out_dir, group_by_genre):
    if group_by_genre:
        paths = glob(os.path.join(inp_dir, '*', '*', '*_conll'))
        fnames = [os.path.basename(path) for path in paths]
        genres = set(re.match(r'([a-z]+)_', fname).group(1) for fname in fnames)
        print('Found %d genres: %s' %(len(genres), ', '.join(genres)))
        for genre in genres:
            genre_out_dir = os.path.join(out_dir, genre)
            copy_folder(inp_dir, genre_out_dir, '%s_' %genre)
    else:
        copy_folder(inp_dir, out_dir, '')


if __name__ == '__main__':
    args = docopt(__doc__)
    main(args['<input_dir>'], args['<output_dir>'], bool(args['--genre']))
    