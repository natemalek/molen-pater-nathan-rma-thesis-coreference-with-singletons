''' Generate a script which when ran will minimize datasets as required by e2e-coref

Usage:
    gencmd_minimize_datasets.py <input_dir> <venv_dir> <script_path> <output_dir>
'''

from docopt import docopt
import shutil
import os
import stat
import sys
import multiprocessing
from utils import grouper_variable_length


def main(inp_dir, venv_dir, bash_file_path, out_dir):
    inp_dir = os.path.abspath(inp_dir) # because we're going to change dir in the bash script
    out_dir = os.path.abspath(out_dir) # because we're going to change dir in the bash script
    cmds = list(generate_commands(inp_dir, out_dir))
    with open(bash_file_path, 'wt') as f: 
        f.write('. ' + os.path.join(venv_dir, 'bin/activate') + ' && \\\n')
        f.write('cd e2e-coref/ \n')
        # I use "&" and "wait" for parallelism here
        # because the jobs are different in size, we can achieve
        # higher speed-up with GNU "parallel"
        # but it's slightly more complicated
        group_size = multiprocessing.cpu_count()
        for group in grouper_variable_length(cmds, group_size):
            for cmd in group:
                f.write('%s & \n' %cmd)
            f.write('wait\n')
        f.write('wait\n')
        f.write('deactivate\n')
    print('Wrote %d commands to %s' %(len(cmds), bash_file_path))


def generate_commands(inp_dir, out_dir):
    '''
    Generate commands that would minimize conll files from inp_dir into
    jsonlines files in out_dir in a parallel directory structure.
    '''
    # base step
    os.makedirs(out_dir)
    for fname in sorted(os.listdir(inp_dir)):
        inp_path = os.path.join(inp_dir, fname)
        out_path = os.path.join(out_dir, fname + '.jsonlines')
        if os.path.isfile(inp_path) and fname.endswith("_conll"):
            yield 'python -u minimize.py %s %s' %(inp_path, out_path)
    # recursive step
    for fname in sorted(os.listdir(inp_dir)):
        inp_path = os.path.join(inp_dir, fname)
        out_path = os.path.join(out_dir, fname)
        if os.path.isdir(inp_path):
            for cmd in generate_commands(inp_path, out_path):
                yield cmd


if __name__ == '__main__':
    args = docopt(__doc__)
    main(args['<input_dir>'], args['<venv_dir>'], args['<script_path>'], args['<output_dir>'])
