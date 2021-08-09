from boto.mturk.connection import MTurkConnection
from io import StringIO
from tqdm import tqdm
from cort.core import corpora
import re
from baselines import Oracle
import sys
import os


def open_mturk_connection(conf):
    conn = MTurkConnection(aws_access_key_id=conf.get_string('AWSAccessKeyId'),
                           aws_secret_access_key=conf.get_string('AWSSecretKey'),
                           host=conf.get_string('requester_host'))
    return conn


def search_hits_by_title(c, title):
    i = 1
    while True:
        hits = c.search_hits(page_size=100, page_number=i)
        if not hits: break
        for h in hits:
            if h.Title == title:
                yield h 
        i += 1
        

def adhoc_fix(path):
    with open(path, 'rb') as f:
        s = f.read()
    s = s.replace(b'\rChrist', b'Christ')
    s = s.replace(b'Christ?\r', b'Christ?')
    s = s.replace(b'output/conll-2012-transformed.v2/men_60/ dev/nw_wsj_00_wsj_0049___part_000.m_auto_conll', 
                  b'output/conll-2012-transformed.v2/men_60/dev/nw_wsj_00_wsj_0049___part_000.m_auto_conll')
    return StringIO(s.decode('utf-8'))


def extract_transformation(conll_path):
    transformation, = re.findall(r'output/conll-2012[-\w\.]+/([-\d\w]+)/dev', conll_path)
    return transformation


def generate_conll_files_for_dataframe(anns, path_gold, path_ann, proj_dir='.', verbose=0):
    if verbose >= 1:
        tqdm.pandas(unit="file")
        apply_func = anns.progress_apply
    else: 
        apply_func = anns.apply
    gold_documents, ann_documents = zip(*apply_func(extract_conll, args=(proj_dir,), axis=1))

    with open(path_gold, 'w') as f:
        corpora.Corpus("gold", gold_documents).write_to_file(f)
    ann_corpus = corpora.Corpus("ann", ann_documents)
    with open(path_ann, 'w') as f:
        ann_corpus.write_to_file(f)
    with open(path_ann + '.ante', 'w') as f:
        ann_corpus.write_antecedent_decisions_to_file(f)


def extract_conll(row, proj_dir='.'):
    conll_path = os.path.join(proj_dir, row['conll_file'])
    #gold_conll_path = os.path.join(proj_dir, "output/original_mentions/conll-2012-transformed/" + "/".join(conll_path.split("/")[-3:]))
    gold_conll_path = conll_path
    try:
        all_chains = [chain.split('=') for chain in 
                row['chains'].replace(' ', '').rstrip('|').split(',')]
        chains = []
        for chain in all_chains:
            if len(chain)>1:
                chains.append(chain)
        # print(row['chains'])
        if not os.path.exists(gold_conll_path):
            gold_conll_path=conll_path
        with open(gold_conll_path, encoding="utf-8") as f:
            gold_corpus = corpora.Corpus.from_file('', f)
            gold_doc = gold_corpus.documents[0]
            Oracle()(gold_doc)
            gold_doc.identifier = gold_conll_path

        with open(conll_path) as f:
            corpus = corpora.Corpus.from_file('', f)
            ann_doc = corpus.documents[0]
            ann_doc.identifier = gold_conll_path
            ann_doc.system_mentions = ann_doc.annotated_mentions
            men_id2obj = {'mention_%d_%d' %(m.span.begin, m.span.end): m 
                        for m in ann_doc.system_mentions}
            for chain_id, chain in enumerate(chains):
                for prev_men_id, men_id in zip([None] + chain[:-1], chain):
                    prev_men = men_id2obj.get(prev_men_id)
                    men = men_id2obj[men_id]
                    men.attributes['set_id'] = chain_id + 1
                    # record as the previous mention in the chain as the antecedent
                    # this is not entirely correct but we didn't instruct our students
                    # to click on any particular mention while selecting a chain so 
                    # it's the best thing we could do.
                    men.attributes['antecedent'] = prev_men
            for men_id, men in men_id2obj.items():
                if men.attributes['set_id'] is None:
                    print('Warning: %s is skipped in document %s' %(men_id, row['conll_file']), file=sys.stderr)
    except:
        print("Error occur at document %s" %row['Document'], file=sys.stderr)
        raise

    return gold_doc, ann_doc
