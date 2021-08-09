from manipulations import Manipulation, syn_mask, ent_mask,\
    delete_subtree, reparse, token_mask, pos_mask
from math import ceil, log10
from utils import spans_over_tokens, str_base
from random import Random
import re

vowel_like = ['u', 'e', 'o', 'a', 'i', 'y', 'ea', 'oo', 'ie', 'ee']
beginning_consonants = list('bcdfghjklmnprstwxz') + ['ch', 'tr', 'th', 'ph', 'sh', 'qu']
ending_consoants = list('cdfgklmnprstx') + ['ch', 'ng'] + [''] * 20
ending_numbers = list(str(i) for i in range(100)) + [''] * 100

def generate_random_identifier(rand=None):
    rand = rand or Random()
    rand_str = (
        rand.choice(beginning_consonants) +
        rand.choice(vowel_like) +
        rand.choice(ending_consoants) +
        rand.choice(ending_numbers) 
    )
    return ('_%s_' % rand_str).upper()


class ReplaceByMaskedToken(object):
    ''' because lambda's don't work with joblib '''
    def __call__(self, name):
        return '<MASKED>'


class RememberingStringMap(object):

    def __init__(self, random_seed, memory=None):
        self.rand = Random(random_seed)
        self.memory = memory or {}

    def __call__(self, name):
        if name not in self.memory:
            new_id = None
            while new_id is None or new_id in self.memory:
                new_id = generate_random_identifier(self.rand)
            self.memory[name] = new_id
        return self.memory[name]


class RandomStringMap(object):

    def __init__(self, random_seed, memory=None):
        self.rand = Random(random_seed)

    def __call__(self, name):
        return generate_random_identifier(self.rand)


def transform_column(func, doc, col, start, stop):
    ''' Apply a function on a column in the document_table of a document 
    and store the results back into that document '''
    if start >= stop: return
    values = [doc.document_table[i][col] for i in range(start, stop)]
    new_values = func(values)
    for i, val in zip(range(start, stop), new_values):
        doc.document_table[i][col] = val


def map_ner(doc, start, stop):
    ''' 
    Remove information in interpretation layers (named-entity recognition,
    syntax, semantic roles) corresponding to a span between (start, stop). 
    '''
    transform_column(lambda vals: [re.sub('\w+', 'UNKN', s) for s in vals], 
                     doc, 10, start, stop)


def mask_span_ner_syn_sem(doc, start, stop):
    ''' 
    Remove information in interpretation layers (named-entity recognition,
    syntax, semantic roles) corresponding to a span between (start, stop). 
    '''
    transform_column(lambda vals: [pos_mask]*len(vals), doc, 4, start, stop) # POS
    transform_column(delete_subtree, doc, 5, start, stop) # syntax
    transform_column(delete_subtree, doc, 10, start, stop) # NER
    mask_semantic_roles(doc, start, stop)


def mask_semantic_roles(doc, start, stop):
    if start >= stop: return
    # find the sentence that contains this span
    sent_span, = [s for s in doc.sentence_spans
                  if s.begin <= start and stop <= s.end+1]
    num_cols = len(doc.document_table[start])
    for col in range(11, num_cols-1):
        tags = [re.sub(r'\*\(\)', '', doc.document_table[i][col])
                for i in range(start, stop)]
        tags = [tag for tag in tags if tag != '']
        if 'V' in tags:
            # if the predicate is gone, its roles are gone too 
            # which applies in the whole sentence, not just the current span
            for i in range(sent_span.begin, sent_span.end+1):
                doc.document_table[i][col] = '*'
        else:
            # just remove roles that are found in the span
            transform_column(delete_subtree, doc, col, start, stop) 
    # clean up the sentence by removing empty columns
    last_sem_col = 11
    for col in range(11, num_cols-1):
        vals = [doc.document_table[i][col] for i in range(sent_span.begin, sent_span.end+1)]
        tag_set = set(re.sub(r'\*\(\)', '', val) for val in vals)
        if tag_set != set(['*']): # non empty column
            for i, val in zip(range(sent_span.begin, sent_span.end+1), vals):
                doc.document_table[i][last_sem_col] = val
            last_sem_col += 1
    for row in doc.document_table[sent_span.begin:sent_span.end+1]:
        while len(row) > last_sem_col+1: 
            # notice that after last_sem_col there's one more column for coreference
            del row[last_sem_col]


def mask_tokens(doc, tokens):
    '''
    Replace tokens with an identifier of choice in doc.document_table.
    If <code>token_map</code> is provided, it will be invoked to get new tokens.
    Otherwises, all tokens are mapped to the same default token mask.
    '''
    spans = spans_over_tokens(doc, tokens)
    for span in spans:
        for i in range(span.begin, span.end+1):
            new_token = token_mask
            doc.document_table[i][3] = new_token
        mask_span_ner_syn_sem(doc, span.begin, span.end+1)


def map_names(doc, tokens, token_map):
    '''
    Replace tokens with an identifier of choice in doc.document_table.
    If <code>token_map</code> is provided, it will be invoked to get new tokens.
    Otherwises, all tokens are mapped to the same default token mask.

    Special case: all speaker identifiers (except trivial ones like "A", "B", "speaker1")
    are mapped as well to accommodate a task where annotators are asked to guess the name
    of entities mentioned in a document.
    '''
    spans = spans_over_tokens(doc, tokens)
    for span in spans:
        for i in range(span.begin, span.end+1):
            new_token = token_map(doc.tokens[i])
            doc.document_table[i][3] = new_token
        map_ner(doc, span.begin, span.end+1)
    for i, speaker in enumerate(doc.speakers[:]):
        if (speaker not in ('-', 'A', 'B', '_Anonymous_') and 
                not speaker.lower().startswith('speaker')):
            doc.document_table[i][9] = token_map(speaker)


class ReplaceNames(Manipulation):
    
    def __init__(self, name_map):
        super(ReplaceNames, self).__init__()
        # because "auto" files might contain POS tagging or NER errors
        self.suffixes = ('_gold_conll',) 
        self.name_map = name_map
        
    def apply_doc(self, doc):
        tokens = [i for m in sorted(doc.system_mentions)
                    for i in range(m.span.begin, m.span.end+1)
                    if doc.pos[i] in ['NNP', 'NNPS']]
        map_names(doc, tokens, self.name_map)
        return reparse(doc)
    

class MaskMentionK(Manipulation):
    
    def __init__(self, k_pct, random_seed):
        super(MaskMentionK, self).__init__()
        self.k_pct = k_pct
        self.rand = Random(random_seed)
        
    def apply_doc(self, doc):
        mention_tokens = [i for m in sorted(doc.system_mentions)
                            for i in range(m.span.begin, m.span.end+1)]
        masked_tokens = self.rand.sample(mention_tokens, 
                                         ceil(len(mention_tokens)*self.k_pct/100))
        mask_tokens(doc, masked_tokens)
        return reparse(doc)
        

class MaskContextK(Manipulation):
    
    def __init__(self, k_pct, random_seed):
        super(MaskContextK, self).__init__()
        self.k_pct = k_pct
        self.rand = Random(random_seed)
        
    def apply_doc(self, doc):
        mention_tokens = [i for m in sorted(doc.system_mentions)
                            for i in range(m.span.begin, m.span.end+1)]
        non_mention_tokens = set(range(len(doc.tokens))).difference(mention_tokens)
        masked_tokens = self.rand.sample(non_mention_tokens, 
                                         ceil(len(non_mention_tokens)*self.k_pct/100))
        mask_tokens(doc, masked_tokens)
        return reparse(doc)
        