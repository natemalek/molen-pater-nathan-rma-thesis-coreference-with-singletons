from nltk.tree import ParentedTree
from utils import *
from cort.core.spans import Span
from cort.core.corpora import Corpus
from nose.tools import *

_tree_str = '''(TOP
  (S
    (PP
      (IN In)
      (NP (NP (DT the) (NN summer)) (PP (IN of) (NP (CD 2005)))))
    (, ,)
    (NP
      (NP (DT a) (NN picture))
      (SBAR
        (WHNP (WDT that))
        (S
          (NP (NNS people))
          (VP
            (VBP have)
            (ADVP (RB long))
            (VP
              (VBN been)
              (VP
                (VBG looking)
                (ADVP (RB forward))
                (S
                  (VP
                    (TO to)
                    (VP
                      (VBD started)
                      (S
                        (VP
                          (VBG emerging)
                          (PP (IN with) (NP (NN frequency)))
                          (PP
                            (IN in)
                            (NP
                              (JJ various)
                              (JJ major)
                              (NML (NNP Hong) (NNP Kong))
                              (NNS media))))))))))))))
    (. .)))'''
_tree = ParentedTree.fromstring(_tree_str)

def read_sample_corpus():
    with open('test/resources/cctv_0001.v4_auto_skel') as f:
        corpus = Corpus.from_file('sample', f)
    # import mention boundaries (but not set IDs)
    for doc in corpus.documents:
        doc.system_mentions = doc.annotated_mentions
    return corpus

test_doc_path = 'test/resources/single-doc.auto_conll'

def read_single_doc_corpus():
    with open(test_doc_path) as f: 
        corpus = Corpus.from_file("masked", f)
        # import mention boundaries (but not set IDs)
        for doc in corpus.documents:
            doc.system_mentions = doc.annotated_mentions
    return corpus

def test_map_values():
  func = lambda x: x + '$'
  assert map_values({}, func) == {}
  assert map_values({1: 'a'}, func) == {1: 'a$'}
  assert map_values({1: 'a', 2: 'b'}, func) == {1: 'a$', 2: 'b$'}


def test_linear_positions():
    compute_linear_positions(_tree)
    b2n = _tree.begin2nodes
    assert len(b2n) == 27
    assert set(hasattr(s, 'span') for s in _tree.subtrees()) == {True}

    assert len(b2n[1]) == 3
    assert ' '.join(b2n[1][0].leaves()) == 'the'
    assert ' '.join(b2n[1][1].leaves()) == 'the summer'
    assert ' '.join(b2n[1][2].leaves()) == 'the summer of 2005'

    assert len(b2n[18]) == 2
    assert ' '.join(b2n[18][0].leaves()) == 'with'
    assert ' '.join(b2n[18][1].leaves()) == 'with frequency'

    s = _tree[(0, 2, 1, 1, 1, 2, 1, 2, 0, 1)]
    assert ' '.join(s.leaves()) == 'started emerging with frequency in various major Hong Kong media'


def test_subtrees_over_span():
    s = subtrees_over_span(_tree, 0, 0)
    assert len(s) == 1
    assert ' '.join(s[0].leaves()) == 'In'
    
    s = subtrees_over_span(_tree, 26, 26)
    assert len(s) == 1
    assert ' '.join(s[0].leaves()) == '.'
    
    s = subtrees_over_span(_tree, 1, 4)
    assert len(s) == 1
    assert ' '.join(s[0].leaves()) == 'the summer of 2005'
    
    s = subtrees_over_span(_tree, 7, 9)
    assert len(s) == 3
    assert ' '.join(s[0].leaves()) == 'picture'
    assert ' '.join(s[1].leaves()) == 'that'
    assert ' '.join(s[2].leaves()) == 'people'
    
    s = subtrees_over_span(_tree, 18, 25)
    assert len(s) == 2
    assert ' '.join(s[0].leaves()) == 'with frequency'
    assert ' '.join(s[1].leaves()) == 'in various major Hong Kong media'

    assert subtrees_over_span(_tree, Span(0, 0)) == subtrees_over_span(_tree, 0, 0) 
    assert subtrees_over_span(_tree, Span(0, 2)) == subtrees_over_span(_tree, 0, 2) 
    assert subtrees_over_span(_tree, Span(20, 26)) == subtrees_over_span(_tree, 20, 26) 


def test_span_subtract():
    assert span_subtract(Span(0, 5), [Span(0, 0)]) == [Span(1, 5)]
    assert span_subtract(Span(0, 5), [Span(5, 5)]) == [Span(0, 4)]
    assert span_subtract(Span(0, 5), [Span(3, 3)]) == [Span(0, 2), Span(4, 5)]
    assert span_subtract(Span(0, 5), [Span(0, 5)]) == []
    assert span_subtract(Span(0, 5), [Span(0, 0), Span(2, 3)]) == [Span(1, 1), Span(4, 5)]
    assert span_subtract(Span(0, 5), [Span(0, 0), Span(1, 3)]) == [Span(4, 5)]
    assert span_subtract(Span(0, 5), []) == [Span(0, 5)]
    assert span_subtract(Span(3, 10), [Span(0, 0)]) == [Span(3, 10)]
    assert span_subtract(Span(3, 10), [Span(5, 5)]) == [Span(3, 4), Span(6, 10)]
    assert span_subtract(Span(3, 10), [Span(6, 10)]) == [Span(3, 5)]
    assert span_subtract(Span(3, 10), [Span(5, 5), Span(7, 9)]) == [Span(3, 4), Span(6, 6), Span(10, 10)]
    assert span_subtract(Span(3, 10), [Span(7, 9), Span(5, 5)]) == [Span(3, 4), Span(6, 6), Span(10, 10)]
    
    
def test_format_conll():
    p = _tree[(0, 2, 1, 1, 1, 2, 1, 2, 0, 1, 1, 0, 2)].copy(deep=True)
    assert ' '.join(p.leaves()) == 'in various major Hong Kong media'
    assert format_conll(p) ==  ['(PP*', '(NP*', '*', '(NML*', '*)', '*))']
    
    
def test_spans_over_tokens():
    doc = sample_corpus.documents[0]
    assert [] == spans_over_tokens(doc, [])
    assert [Span(0, 0)] == spans_over_tokens(doc, [0])
    assert [Span(4, 4)] == spans_over_tokens(doc, [4])
    assert [Span(5, 5)] == spans_over_tokens(doc, [5])
    assert [Span(17, 17)] == spans_over_tokens(doc, [17])
    assert [Span(5, 5), Span(8, 8)] == spans_over_tokens(doc, [5, 8])
    assert [Span(5, 6), Span(8, 8)] == spans_over_tokens(doc, [5, 6, 8])
    assert [Span(5, 8)] == spans_over_tokens(doc, [5, 6, 7, 8])
    assert [Span(4, 4), Span(5, 5)] == spans_over_tokens(doc, [4, 5])
    
def test_grouper():
    assert list(grouper(["a", "b"], 1)) == [("a",), ("b",)]
    assert list(grouper(["a", "b", "c", "d"], 2)) == [("a", "b"), ("c", "d")]
    
@raises(Exception)
def test_grouper_uneven():
    grouper(["a", "b", "c"], 2)

def test_str_base():
    assert str_base(224,15) == 'ee'
    assert str_base(720, 36) == 'k0'
    assert str_base(1295, 36) == 'zz'
    assert str_base(18144, 36) == 'e00'
    assert str_base(-1, 20) == '-1'
    assert str_base(-29, 29) == '-10'
