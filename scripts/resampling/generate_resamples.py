'''
Resample corpora in a consistent way. As input, you give a folder that contains
many version of the same corpora. The program will select the same set of documents for
each version and create resample folders with the same structure as the original one.

Usage:
    generate_resamples.py --dsname=<n> <inp_dir> <out_dir>
'''
from docopt import docopt
from cort.core.corpora import Corpus
import os
import numpy as np
from functools import reduce
from baselines import copy_gold_annotations
from tqdm import tqdm
import re

def main(dsname, inp_dir, out_dir):
    version_names = sorted(os.listdir(inp_dir))
    corpus_versions = {ver: read_docs(os.path.join(inp_dir, ver, dsname), ver)
                       for ver in version_names}
    doc_identifiers = get_doc_identifiers(corpus_versions)
    rng = np.random.RandomState(7284)
    samples = rng.choice(doc_identifiers, size=(25, len(doc_identifiers)), replace=True)
    for sample_no, sample in enumerate(samples):
        sample_dir = os.path.join(out_dir, 'sample_%02d' % sample_no)
        for ver, corpus in tqdm(corpus_versions.items()):
            out_dir_ver = os.path.join(sample_dir, ver)
            os.makedirs(out_dir_ver)
            with open(os.path.join(out_dir_ver, dsname), 'w') as f:
                for i, doc_id in enumerate(sample):
                    if doc_id in corpus:
                        doc = corpus[doc_id]
                        # It is necessary to replace the part number because the
                        # official scorer use a dictionary keyed on doc ID to store 
                        # results. 
                        # It is also necessary to update the second column to match
                        # otherwise the overly careful e2e will break on an assertion
                        doc.identifier = re.sub(r'\d+$', '%04d' %i, doc_id)
                        for row in doc.document_table:
                            row[1] = str(i)
                        # because the same Document object is reused, we need to 
                        # write it out to file right away
                        # (I tried deepcopy but it leads to complications)
                        f.write(doc.get_string_representation())
                    else:
                        print('Ignored document "%s" in version "%s"' %(doc_id, ver))


def read_docs(path, name=''):
    with open(path) as f:
        corpus = Corpus.from_file(name, f)
    for doc in corpus:
        # so that the gold annotations are written out
        copy_gold_annotations(doc)
    return {doc.identifier: doc for doc in corpus}
        

def get_doc_identifiers(corpus_versions):
    doc_identifier_sets = [set(corpus.keys()) for corpus in corpus_versions.values()]
    all_doc_identifiers = reduce(lambda a, b: a.union(b), doc_identifier_sets)
    return np.array(list(sorted(all_doc_identifiers)))


if __name__ == '__main__':
    args = docopt(__doc__)
    main(args['--dsname'], args['<inp_dir>'], args['<out_dir>'])