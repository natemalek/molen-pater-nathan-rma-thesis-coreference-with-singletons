from cort.core import corpora, external_data
import codecs
import re
import os
import sys
from cort.core.documents import CoNLLDocument
from utils import subtrees_over_span, span_subtract,\
    remove_linear_positions, format_conll, add_system_set_ids, spans_over_tokens
from cort.core.spans import Span
from cort.core.corpora import Corpus
import shutil
import traceback

# so that annonymized names won't change
token_mask = '<MASKED>'
pos_mask = '<MASKED>'
syn_mask = 'NOPARSE'
ent_mask = 'NONE'

def progress(it):
    for i, val in enumerate(it):
        yield val
        if (i+1) % 100 == 0: 
            sys.stderr.write('%d...\n' %(i+1))

def write_html(f, doc, highlighted_mentions=None):
    """ 
    Convert the document into a simple HTML representation with relevent
    mentions highlighted for manual inspection. If no mentions are provided,
    highlight all mentions.
    """
    highlighted_mentions = highlighted_mentions or doc.system_mentions
    content = ['_' if tok == token_mask else tok for tok in doc.tokens]
    for mention in highlighted_mentions:
        tag_begin = "<span style=\"color:red\" title=\""
        tag_begin += "e:" + str(mention.attributes["set_id"]) + " "
        tag_begin += "\">["
        old_begin = content[mention.span.begin]
        content[mention.span.begin] = tag_begin + old_begin
        content[mention.span.end] += "]</span>"
    for sentence_span in doc.sentence_spans:
        speakers = set(doc.speakers[j] for j in range(sentence_span.begin, sentence_span.end+1))
        if len(speakers) > 1:
            speaker = '&lt;Multiple Speakers&gt;'
        else:
            speaker = re.sub('^-$', '&lt;Unknown Speaker&gt;', next(iter(speakers)))
        content[sentence_span.begin] = speaker + ': ' + content[sentence_span.begin]
        content[sentence_span.end] = content[sentence_span.end] + "<br/>\n"
    for s in content: 
        f.write(s)
        f.write(' ')

def find_char_n(ch, s, n, rev=False):
    ''' Find the n-th occurrence of a character in a string '''
    if rev:
        it = range(len(s)-1, -1, -1)
    else:
        it = range(len(s))
    for i in it:
        if s[i] == ch: n -= 1
        if n == 0: return i
    return -1

class Manipulation(object):
    
    def __init__(self):
        self.reset_counters()
        self.suffixes = ('_auto_conll', '_gold_conll')

    def reset_counters(self):
        self.total_corpora = 0
        self.read_corpora = 0
        self.availabe_documents = 0
        self.transformed_documents = 0

    def apply_doc(self, doc):
        return doc # no changes
    
    def __call__(self, inp_dir, out_dir):
        '''
        Handle the logics that is common to all manipulations: opening files,
        writing results, presenting in HTML format.
        '''
        if os.path.exists(out_dir): shutil.rmtree(out_dir)
        os.makedirs(out_dir)
        for suffix in self.suffixes:
            for inp_path, corpus in progress(self.iterate_corpora(inp_dir, suffix)):
                for doc in corpus:
                    # parallelism could have been applied here for better performance
                    # however, that would make corpora non-deterministic because of 
                    # the interaction between multi-processing and pseudo-random generation
                    self.availabe_documents += 1
                    if not doc.system_mentions:
                        sys.stderr.write("Document doesn't contain any mention: %s\n" %doc.identifier)
                    else:
                        new_doc = self.apply_doc(doc)
                        if new_doc is None:
                            print('Failed to apply transformation, ignored one document in file: %s' %inp_path, sys.stderr)
                        else: 
                            new_doc.system_mentions = new_doc.annotated_mentions
                            add_system_set_ids(new_doc)
                            
                            if doc.identifier: 
                                basename = re.sub('^_', '', re.sub('[/(); ]', '_', doc.identifier))
                                basename += '.m' + suffix
                                conll_path = os.path.join(out_dir, basename)
                                with codecs.open(conll_path, 'w', "utf-8") as f_conll:
                                    new_corpus = Corpus(corpus.description, [])
                                    new_corpus.documents.append(new_doc)
                                    new_corpus.write_to_file(f_conll)
                                html_path = os.path.join(out_dir, basename + '.html')
                                with codecs.open(html_path, 'w', "utf-8") as f_html:
                                    write_html(f_html, new_doc)
                                self.transformed_documents += 1
                            else: 
                                # without an identifier, one file will overwrite another
                                print('Missing doc identifier, ignored one document in file: %s' %inp_path, sys.stderr)
        return self

    def iterate_corpora(self, dir_or_file, suffix, verbose=True):
        '''
        Iterate throw all corpora in a directory (or a file). Return iterator of
        pairs of <path: str, cort.core.corpora.Corpus>.
        '''
        if os.path.isfile(dir_or_file):
            self.total_corpora += 1
            yield dir_or_file, self.read_corpus(dir_or_file, verbose)
            self.read_corpora += 1
        else:
            # everything is sorted to keep a fixed order
            # different orders will lead to different results because of pseudo-randomness
            for fname in sorted(os.listdir(dir_or_file)):
                if re.search('%s$' %re.escape(suffix), fname):
                    self.total_corpora += 1
                    path = os.path.join(dir_or_file, fname)
                    corpus = None
                    try:
                        corpus = self.read_corpus(path, verbose)
                        self.read_corpora += 1
                    except:
                        # https://github.com/dmcc/PyStanfordDependencies/issues/24
                        sys.stderr.write("Ignored due to parsing error: %s\n" %path)
                        traceback.print_exc(file=sys.stderr)
                    if corpus != None:
                        # if we move yield inside try... except, it will catch the
                        # GeneratorExit exception and disturb the generator flow
                        yield path, corpus

    def read_corpus(self, path, verbose=True):
        if verbose:
            print('Reading %s... ' %path)
        with codecs.open(path, 'r', "utf-8") as f: 
            corpus = Corpus.from_file("reference", f)
        for doc in corpus: 
            doc.system_mentions = doc.annotated_mentions
            for m in doc.system_mentions: 
                m.attributes['set_id'] = m.attributes['annotated_set_id']
        return corpus

    def print_report(self):
        print('Read %d in %d corpora' %(self.read_corpora, self.total_corpora))
        print('Transformed %d in %d read documents' %(self.transformed_documents, self.availabe_documents))


def mask_names(doc, rand):
    gender_data = external_data.GenderData.get_instance()
    unique_names = set()
    unique_names.update(doc.speakers)
    unique_names.update(doc.tokens[i] for i in range(len(doc.pos)) 
                        if doc.pos[i] in ['NNP', 'NNPS'])
    unique_names = list(unique_names)
    rand.shuffle(unique_names)
    name_map = {}
    for name in unique_names:
        new_name = 'Name%03d' %len(name_map)
        gender = gender_data.word_to_gender.get(name.lower())
        if gender in ("MALE", "FEMALE", "PLURAL"):
            new_name = gender[0] + new_name
        name_map[name] = new_name
    for i in range(len(doc.document_table)):
        if doc.pos[i] in ['NNP', 'NNPS']:
            doc.document_table[i][3] = name_map[doc.tokens[i]]
        doc.document_table[i][9] = name_map[doc.speakers[i]]

def remove_propositions(doc):
    for row in doc.document_table:
        row[6] = row[7] = '_'
        del row[11:len(row)-1]

def outermost_mentions(doc):
    mentions = sorted(doc.system_mentions)
    for i in range(len(mentions)-1, -1, -1):
        containing_men = None
        if (i < len(mentions)-1 and
                mentions[i+1].span.begin == mentions[i].span.begin and
                mentions[i+1].span.end >= mentions[i].span.end):
            containing_men = i+1
        else:
            for j in range(i):
                if (mentions[j].span.begin <= mentions[i].span.begin and
                        mentions[j].span.end >= mentions[i].span.end):
                    containing_men = j
                    break
        if containing_men is not None:
            del mentions[i]
    return mentions

def remove_unmatched_ner_parenthese(rows):
    col = 10 # see http://conll.cemantix.org/2012/data.html
    parenthese = []
    for r, row_strs in enumerate(rows):
        for i, ch in enumerate(row_strs[col]):
            assert len(ch) == 1
            if ch == '(':
                parenthese.append((r, i, ch))
            elif ch == ')':
                if parenthese and parenthese[-1][2] == '(':
                    del parenthese[-1]
                else:
                    parenthese.append((r, i, ch))
    for r, i, ch in sorted(parenthese, reverse=True):
        if ch == '(': 
            m = re.search(r'\(\w+', rows[r][col])
            assert m
            tag = m.group()
            rows[r][10] = rows[r][10][:i] + rows[r][col][i+len(tag):]
        elif ch == ')':
            rows[r][10] = rows[r][10][:i] + rows[r][col][i+1:]
        else: 
            raise ValueError("Don't know what to do with this symbol: %s" %ch)
 

def delete_subtree(syntax_by_token):
    '''
    Delete all the subtrees that are completely contained in 
    '''
    assert len(syntax_by_token) > 0
    # implementation idea: remove subtrees from smallest to biggest
    syntax_by_token = syntax_by_token[:] # copy
    one_token_subtree = r'\([\w-]+\s*\*?\s*\)'
    multi_token_subtree_open = r'\(([\w-]+)\*$'
    multi_token_subtree_close = r'^\*\)'
    for i in range(len(syntax_by_token)):
        syntax_by_token[i] = re.sub(one_token_subtree, '*', 
                                    syntax_by_token[i])
    for k in range(1, len(syntax_by_token)):
        for i in range(len(syntax_by_token)-k):
            no_nested_subtree = all(syntax_by_token[j] == '*' for j in range(i+1, i+k))
            openning_match = re.search(multi_token_subtree_open, syntax_by_token[i])
            closing_match = re.search(multi_token_subtree_close, syntax_by_token[i+k])
            if (no_nested_subtree and openning_match and closing_match
                    and openning_match.group(1) != 'TOP'):
                syntax_by_token[i] = re.sub(multi_token_subtree_open, '*', syntax_by_token[i])
                syntax_by_token[i+k] = re.sub(multi_token_subtree_close, '*', syntax_by_token[i+k])
    return syntax_by_token

def mask_span(doc, start, stop):
    if start >= stop: return
    syntax = [doc.document_table[i][5] for i in range(start, stop)]
    syntax = delete_subtree(syntax)
    ner = [doc.document_table[i][10] for i in range(start, stop)]
    ner = delete_subtree(ner)
    for i in range(start, stop):
        doc.tokens[i] = doc.document_table[i][3] = token_mask
        doc.document_table[i][4] = pos_mask
        doc.document_table[i][5] = syntax[i-start]
        doc.document_table[i][10] = ner[i-start]


def reparse(doc):
    ''' Create a new document object with information in doc.document_table '''
    new_doc_table = [['#begin document %s' %doc.identifier]]
    for sent_span in doc.sentence_spans:
        rows = doc.document_table[sent_span.begin:sent_span.end+1]
        new_doc_table.extend(rows)
        new_doc_table.append([])
    new_doc_table.append(['#end document'])
    try:
        return CoNLLDocument('\n'.join('\t'.join(f for f in row) 
                                       for row in new_doc_table))
    except KeyError:
        # https://github.com/dmcc/PyStanfordDependencies/issues/24
        sys.stderr.write("Skipped document %s due to error.\n" %doc.identifier)
        traceback.print_exc(file=sys.stderr)
        return None

