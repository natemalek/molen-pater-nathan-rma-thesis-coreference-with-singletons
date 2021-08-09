from random import Random
from manipulations2 import *
import shutil
import os
from collections import Counter
from cort.core.corpora import Corpus
from nose.tools import assert_equals


test_doc_path = 'test/resources/single-doc.auto_conll'


def get_auto_conll_path(dir_):
    paths = [p for p in os.listdir(dir_) if p.endswith('_auto_conll')]
    assert len(paths) == 1
    return os.path.join(dir_, paths[0])


def setup_module(module):
    shutil.rmtree('test/tmp2', ignore_errors=True)
    os.mkdir('test/tmp2')


def test_memory_token_map():
    token_map = RememberingStringMap(13238)
    a_name = token_map('a')
    b_name = token_map('b')
    a_name2 = token_map('a')
    assert isinstance(a_name, str)
    assert isinstance(b_name, str)
    assert a_name == a_name2
    assert a_name != b_name


def test_name_replacement():
    func = ReplaceNames(RememberingStringMap(1522))
    out_dir = 'test/tmp2/test_name_replacement'
    func(test_doc_path, out_dir)
    with open(get_auto_conll_path(out_dir)) as f:
        doc_str = f.read()
    names = re.findall(r'_\w+_', doc_str)
    counts = Counter(names)
    assert len(names) > 20
    # "Hong" and "Kong" occur 10 times in the original document
    assert any(c == 10 for c in counts.values()) 
    # "Disney" occurs 12 times in the original document
    assert any(c == 12 for c in counts.values())

    with open(get_auto_conll_path(out_dir)) as f:
        doc, = Corpus.from_file("masked", f).documents
    mention_ner = [row[10] for row in doc.document_table 
                   if re.match(r'_\w+_$', row[3]) # name is replaced
                       and row[-1] != '*'] # coreference group is set
    assert_equals(set(mention_ner), set(['(UNKN*', '*)', '(UNKN)', '*']))


def test_nonmention():
    out_dir = 'test/tmp2/test-nonmention'
    MaskContextK(100, 2352)('test/resources/nt_4212.v4_gold_skel', out_dir)
    with open(get_auto_conll_path(out_dir)) as f: 
        corpus = Corpus.from_file("masked", f)
    assert len(corpus.documents) == 1
    doc = corpus.documents[0]
    syntax_tags = [row[5] for row in doc.document_table]
    top_tag, top_cnt = Counter(syntax_tags).most_common(1)[0]
    assert top_tag == '*' and top_cnt >= 20


def test_mention():
    out_dir = 'test/tmp2/test-mention'
    MaskMentionK(100, 34822)('test/resources/nt_4212.v4_gold_skel', out_dir)
    with open(get_auto_conll_path(out_dir)) as f: 
        corpus = Corpus.from_file("masked", f)
    assert len(corpus.documents) == 1
    doc = corpus.documents[0]
    syntax_tags = [row[5] for row in doc.document_table if row[3] == '<MASKED>']
    assert syntax_tags == ['(TOP(S*', '*', '(SBAR(S*', '(S*', '(SBAR(S*']


def test_replicability():
    out_dir1 = 'test/tmp2/test-mention-replicability1'
    out_dir2 = 'test/tmp2/test-mention-replicability2'
    MaskContextK(0.5, 1)(test_doc_path, out_dir1)
    MaskContextK(0.5, 1)(test_doc_path, out_dir2)
    with open(get_auto_conll_path(out_dir1)) as f1, \
            open(get_auto_conll_path(out_dir2)) as f2:
        assert f1.read() == f2.read()
        

def test_mask_span_ner_syn_sem():
    with open(test_doc_path) as f:
        doc = Corpus.from_file('', f).documents[0]
    mask_span_ner_syn_sem(doc, 0, 5)
    rows = doc.document_table[:5]
    print(rows)
    assert [row[3] for row in rows] == 'In the summer of 2005'.split() # tokens
    assert set(row[4] for row in rows) == set(['<MASKED>']) # POS
    assert [row[5] for row in rows] == ['(TOP(S*', '*', '*', '*', '*'] # syntax
    assert set(row[10] for row in rows) == set(['*']) # NER
