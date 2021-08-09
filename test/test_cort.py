from cort.core.corpora import Corpus
from utils import add_system_set_ids
import re

test_doc_path = 'test/resources/single-doc.auto_conll'


def _extract_content(doc_str):
    lines = re.sub('[\t ]+', ' ', doc_str).splitlines()
    return [l.strip() for l in lines if l]


def test_read_and_write():
    out_path = 'test/tmp/read_and_write.conll'
    with open(test_doc_path) as f: 
        corpus = Corpus.from_file("masked", f)
        for doc in corpus.documents:
            doc.system_mentions = doc.annotated_mentions
            add_system_set_ids(doc)
    with open(out_path, 'w') as f:
        corpus.write_to_file(f)
    with open(test_doc_path) as f1, open(out_path) as f2:
        doc1 = _extract_content(f1.read())
        doc2 = _extract_content(f2.read())
        assert doc1 == doc2


def test_repeated_read_and_write():
    for i in range(5):
        out_path = 'test/tmp/repeated_read_and_write-%d.conll' %i
        with open(test_doc_path) as f: 
            corpus = Corpus.from_file("masked", f)
        with open(out_path, 'w') as f:
            corpus.write_to_file(f)
    doc_str = None
    for i in range(5):
        path = 'test/tmp/repeated_read_and_write-%d.conll' %i
        with open(path) as f:
            s = f.read()
            assert doc_str is None or doc_str == s
            doc_str = s
