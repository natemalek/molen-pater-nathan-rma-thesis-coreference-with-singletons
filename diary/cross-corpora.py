import os
import re

root_dir = '/Users/cumeo/corpora'
word_count = 0
with open('cross-corpora.txt', 'rt') as f: 
    for line in f:
        file1, file2 = line.strip().split('\t')
        with open(os.path.join(root_dir, file1+'.plain'), 'rt') as f2:
            word_count += len(re.split('\s+', f2.read().strip()))
print word_count
